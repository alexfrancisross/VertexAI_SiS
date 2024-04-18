--Snowflake External Access + Vertex GenAI API Demo
--This demo shows how to use External Access in Snowflake to call the Vertex GenAI Palm2 LLM: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/text
--Author Alex Ross, Senior Sales Engineer, Snowflake
--Last Modified 16th April 2024

--Create demo database/schema
USE ROLE ACCOUNTADMIN;
USE DATABASE DEMOS;
CREATE OR REPLACE SCHEMA VERTEX;

--Create Security Integration For GCP OAuth
--Visit https://console.cloud.google.com/apis/credentials to generate OAuth 2.0 Client IDs
CREATE OR REPLACE SECURITY INTEGRATION vertex_access_integration
  TYPE = API_AUTHENTICATION
  AUTH_TYPE = OAUTH2
  OAUTH_CLIENT_ID = '<YOUR CLIENT ID>'
  OAUTH_CLIENT_SECRET = '<YOUR CLIENT SECRET>'
  OAUTH_TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'
  OAUTH_AUTHORIZATION_ENDPOINT = 'https://accounts.google.com/o/oauth2/auth'
  OAUTH_ALLOWED_SCOPES = ('https://www.googleapis.com/auth/cloud-platform', 'https://europe-west2-aiplatform.googleapis.com')
  ENABLED = TRUE;
GRANT ALL ON INTEGRATION vertex_access_integration to ROLE PUBLIC;

--Create Secret to hold GCP OAuth refresh token
--Visit https://developers.google.com/oauthplayground/ to generate OAuth refresh token using client ID and secret 
CREATE OR REPLACE SECRET vertex_oauth_token
TYPE = OAUTH2
API_AUTHENTICATION = vertex_access_integration
OAUTH_REFRESH_TOKEN ='<YOUR OAUTH REFRESH TOKEN>';
GRANT USAGE ON SECRET vertex_oauth_token to role PUBLIC;
GRANT READ ON SECRET vertex_oauth_token to role PUBLIC;

--Create Network Rule to allow connectivity with Google API endpoints
CREATE OR REPLACE NETWORK RULE gcp_apis_network_rule
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ('europe-west2-aiplatform.googleapis.com','oauth2.googleapis.com','accounts.google.com','www.googleapis.com:443');
  
--Create The External Access Integration
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION GCP_APIS_ACCESS_INTEGRATION
  ALLOWED_NETWORK_RULES = (gcp_apis_network_rule)
  ALLOWED_AUTHENTICATION_SECRETS = (vertex_oauth_token)
  ENABLED = true;
GRANT ALL ON INTEGRATION GCP_APIS_ACCESS_INTEGRATION TO ROLE PUBLIC;

--Create SP to handle Rest API call to Vertex GenAI endpoint
--Returns a string response based on prompt and parameters provided to the SP 
CREATE OR REPLACE PROCEDURE GET_VERTEX_TEXT_GENERATION("PROMPT" VARCHAR(16777216), "TEMPERATURE" FLOAT, "MAX_OUTPUT_TOKENS" NUMBER(38,0), "TOP_P" FLOAT, "TOP_K" FLOAT)
RETURNS VARCHAR(16777216)
LANGUAGE PYTHON
RUNTIME_VERSION = '3.8'
PACKAGES = ('snowflake-snowpark-python','requests')
HANDLER = 'get_text_generation'
EXTERNAL_ACCESS_INTEGRATIONS = (GCP_APIS_ACCESS_INTEGRATION)
SECRETS = ('cred'=VERTEX_OAUTH_TOKEN)
EXECUTE AS OWNER
AS '
import _snowflake
import requests
import json

def get_text_generation(session, prompt, temperature, max_output_tokens, top_p, top_k):
    PROJECT_ID=''<YOUR GCP PROJECT>''
    LOCATION=''europe-west2''
    token = _snowflake.get_oauth_access_token(''cred'')
    url = f''https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/text-bison:predict''
    d = {''instances'':[{''prompt'': prompt}],
         ''parameters'':{''temperature'': temperature,
                ''maxOutputTokens'': max_output_tokens,
                ''topK'': top_k,
                ''topP'': top_p
            }
        }
    h = {
            ''Authorization'': ''Bearer '' + token,
            ''Content-Type'': ''application/json; charset=utf-8''
        }

    try:
        response = requests.post(url, data=json.dumps(d), headers=h)
        data = response.json()
        return data[''predictions''][0][''content'']
    except:
        return data
';

call get_vertex_text_generation('why is snowflake the best data platform?',0.2,256,0.95,2); --Test SP is working as expected

--Create a UDF to handle Rest API call to Vertex GenAI endpoint
--This UDF is designed to be used to analyse a customer review
--Returns a variant/json response based on prompt and parameters provided to the UDF 
CREATE OR REPLACE FUNCTION GET_VERTEX_REVIEW_SENTIMENT_UDF("PROMPT" VARCHAR(16777216), "TEMPERATURE" FLOAT, "MAX_OUTPUT_TOKENS" NUMBER(38,0), "TOP_P" FLOAT, "TOP_K" FLOAT)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.8'
PACKAGES = ('snowflake-snowpark-python','requests')
HANDLER = 'GET_VERTEX_REVIEW_SENTIMENT'
EXTERNAL_ACCESS_INTEGRATIONS = (GCP_APIS_ACCESS_INTEGRATION)
SECRETS = ('cred'=VERTEX_OAUTH_TOKEN)
AS '
import _snowflake
import requests
import json

def GET_PREPROMPT():
    preprompt = ''For the given review, return a JSON object that has the fields sentiment, explanation, summary, and product. Acceptable values for sentiment are Positive or Negative. The explanation field contains text that explains the sentiment. The summary field contains a single sentence summarizing the review in under 10 words. The product field contains the name or type of product purchased if it has been included in the review. DO NOT INCLUDE BACKTICKS IN THE RESPONSE. Review: ''
    return preprompt

def GET_VERTEX_REVIEW_SENTIMENT(prompt, temperature, max_output_tokens, top_p, top_k):
    PROJECT_ID=''<YOUR GCP PROJECT>''
    LOCATION=''europe-west2''
    token = _snowflake.get_oauth_access_token(''cred'')
    url = f''https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/text-bison:predict''
    d = {''instances'':[{''prompt'': GET_PREPROMPT() + prompt}],
         ''parameters'':{''temperature'': temperature,
                ''maxOutputTokens'': max_output_tokens,
                ''topK'': top_k,
                ''topP'': top_p
            }
        }
    h = {
            ''Authorization'': ''Bearer '' + token,
            ''Content-Type'': ''application/json; charset=utf-8''
        }

    try:
        response = requests.post(url, data=json.dumps(d), headers=h)
        data = response.json()
        return json.loads(data[''predictions''][0][''content''])
    except:
        return data
';
GRANT USAGE ON FUNCTION GET_VERTEX_REVIEW_SENTIMENT_UDF(VARCHAR(16777216), FLOAT, NUMBER(38,0), FLOAT, FLOAT) TO ROLE PUBLIC;

select GET_VERTEX_REVIEW_SENTIMENT_UDF('This is a shoe I will wear with black dress pants or jeans when I need comfort and a little style, but I am not impressed. This is a very flimsy shoe with little support at all. Unlike any other shoes I''ve purchased in the past. It looks nice, but it''s not comfortable.',0.2,256,0.95,2) as RESPONSE; --Test UDF

--Upload sample file 'Customer_Reviews.csv' to table DEMOS.VERTEX.REVIEWS 
select *, GET_VERTEX_REVIEW_SENTIMENT_UDF(REVIEW,0.2,256,0.95,2) AS VERTEX_REVIEW_VAR, VERTEX_REVIEW_VAR:sentiment AS VERTEX_SENTIMENT, VERTEX_REVIEW_VAR:explanation AS VERTEX_EXPLANATION, VERTEX_REVIEW_VAR:product AS VERTEX_PRODUCT, VERTEX_REVIEW_VAR:summary AS VERTEX_SUMMARY
FROM DEMOS.VERTEX.REVIEWS sample(5 rows); --Test UDF using a table with 10 records of customer review data