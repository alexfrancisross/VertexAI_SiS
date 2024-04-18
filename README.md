# Vertex AI SiS App
Sample app using Snowflake External Access, Streamlit in Snowflake, and Vertex AI 

For more information please see this related blog post: https://cloudydata.substack.com/p/snowflake-and-vertex-ai-foundational

This repo contains a sample a Streamlit in Snowflake app that uses External Access to call Vertex AI Palm2 for TextGeneration: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/text

**1. Customer_Reviews.csv:** A csv file containing fictitious customer reviews for a retailer (upload this to a table named DEMOS.VERTEX.REVIEWS using Snowsight).

**2. Vertex_Demo.sql:** A sample script that demonstrates how to create a Stored Procedure/UDF that calls the TextGeneration Vertex API endpoint using the PaLM2 for Text (text-bison) foundational model which is ideal for tasks that can be completed with one API response: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/text. The script includes the code for creating a Snowflake Security Integration, Secret, Network Rule, and External Access Integration used by the Stored Procedure.

**3. VertexAI_Text_Gen_SiS.py:** A ‘test harness’ UI for calling the Stored Procedure created in Step 2. This is a modified version of a standalone Streamlit application available from Google’s Github Repo here. 

**4. Customer_Review_Analyser_SiS.py:** An example Streamlit in Snowflake application that provides a user with the ability to analyse/filter customer reviews stored in a Snowflake table and uses Vertex AI to summarize the review, perform sentiment analysis, and extract product information.

