# LudusSMA

## INTRODUCTION
LudusSMA aims to help board game clubs with Instagram. The main goal is to automate the creation of stories to remind followers of events the association is participating in, as well as to manage the association's Instagram account without the need to access Instagram itself.

With the aim of automating the creation of stories, some macro categories of events can be created. The idea in this case is to create formats so that a certain type of event will always have the same background image and have more consistency. For example, you can choose a specific image to be associated with "Bang! Tournaments". That way, every time a story is posted to remind followers of the upcoming tournaments, that image will be used as the background. More details about the specific event will be added to the story, including the date, time, and location.

These macro categories are called _Event Types_.

Then the bot user can add events that must belong to some _event_type_. With reference to the previous example, _Bang Tournament_ is the event type, then the _event_ is some Bang Tournament on March 7th, from 14 to 20, in Verona.


Its functionalities include

- Create and manage event categories, such as tournaments or festivals;
- Create specific events and Instagram Stories to remind followers of them;
- Create individual posts or stories, complete with images and descriptions (WIP)
## ARCHITECTURE

The whole architecture is based on AWS

![here](/Documentation/architecture.png)

### Clarification

The entire architecture is based as much as possible on the concept of zero-budget, which is why more performative or self-managed resources were not used, such as Secret Manager instead of Parameter Store, or why a bot was chosen to take updates in push via webhook and Lambda Function instead of in pull as is normally done for Telegram bots perhaps via Docker image and services such as ECS or AppRunner.
This clearly increased the architectural complexity, but got to a point where the only important costs are given by the elaboration of the text and image by LLMs.

## OVERALL BOT STRUCTURE

![Bot Flow](/Documentation/bot_flow.png)

## CREATE YOUR OWN SOCIAL MEDIA ASSISTANT

### Step 1: Create Your Telegram Bot
To create your bot on Telegram, follow the official guide [here](https://core.telegram.org/bots/features#creating-a-new-bot). After completing this step, you'll obtain the token, which is essential for setting up the webhook that allows Telegram to send updates to the AWS Lambda Function. This will be the final step in the guide.

### Step 2: Get Meta API Tokens
You will also need the API tokens from Meta for your Instagram account, which must be a Business account. @Riccardo

### Step 3: Fork This Repository
Fork this repository to set up the entire CI/CD service automatically and configure the secrets used by the underlying architecture.

#### Prerequisites
Before proceeding, ensure you meet the following prerequisites:

- **AWS Account**: You must have an AWS account and set up local credentials with sufficient permissions to create resources (CodePipeline, CodeBuild, IAM Roles and Policies, etc.). Refer to the [AWS CLI Authentication Guide](https://docs.aws.amazon.com/cli/v1/userguide/cli-chap-authentication.html).
- **AWS CLI Installed**: Install the AWS CLI by following the instructions [here](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).
- **Terraform Installed**: Install Terraform by following the instructions [here](https://developer.hashicorp.com/terraform/install).

#### Step 4: Create `secret.json`
Create a `secret.json` file in the `tf_foundation` folder. This file should never be committed to the repository as it only initializes the secrets. The file should have the following structure:

```json
{
    "/meta/access-token": "***",
    "/meta/client-secret": "***",
    "/telegram/allow-chat-ids": "***,***",
    "/telegram/bot-token": "***",
    "/telegram/header-webhook-token": "***"
}
```

Note that `/telegram/allow-chat-ids` should be a string of chat IDs separated by commas.

#### Step 5: Update Variables
In the [variables.tf](/tf_foundation/variables.tf) file, update the variables with the correct repository name and branch. You can also update the resource tags and deployment region.

#### Step 6: Initialize Terraform
Once everything is set up, open a terminal in the root folder of the repository and run the following commands:

```bash
cd tf_foundation
terraform init
terraform plan -out=plan.tfplan
terraform apply plan.tfplan
```

#### Step 7: Connect AWS to GitHub
After the foundation is created, manually connect AWS to GitHub by following [this guide](https://docs.aws.amazon.com/dtconsole/latest/userguide/connections-update.html).

#### Foundation Management
The foundation is now ready and shouldn't be modified again. Any further deployment will reset the secrets with the original values, which might have been rotated by the custom Lambda function, potentially breaking the bot. If the foundation needs to be updated, remember to update the `secret.json` file with the correct current values.

From this point forward, every commit to the selected branch will trigger the pipeline, which will create or update the architecture using Terraform.

#### Customization
There are a few areas that need to be customized:

- In the [variables.tf](terraform/variables.tf) file, update the `developers_email` variable with the correct email addresses.
- In the [vocabulary.txt](vocabulary.txt) file, update the technical jargon as needed.

Once these aspects are customized, commit to the repository, and the release pipeline will automatically start, creating or updating the entire architecture.

### Step 8: Set Up the Telegram Webhook
The last step is to set up the Telegram webhook and security token. This can be done via Postman, a Python script with the `requests` library, or directly using `curl` in the terminal. Here's the command for convenience:

```bash
curl --location 'https://api.telegram.org/{{bot-token}}/setWebhook' \
--data '{
    "url": "{{auth-lambda-trigger}}",
    "max_connections": 10,
    "allowed_updates": "message",
    "drop_pending_updates": true,
    "secret_token":"{{secret-token}}"
}'
```

**You're All Set!**

Enjoy your new Social Media Assistant Bot!

### DEBUGGING

The most important point that you would like to be able to modify is the logic of the bot itself. To do this you need to modify the code in [lambda_telegram_bot](lambda_telegram_bot/) folder. In particular, in the file [main](lambda_telegram_bot/main.py) an entrypoint is already set up for which the bot can be used by polling.

You just need to use the following configuaration for VSCode in `launch.json`.
```json
{
    "name": "Module: Telegram Bot",
    "type": "debugpy",
    "request": "launch",
    "module": "lambda_telegram_bot.main",
    "env":{
        "IAM_ROLE_EVENT_SCHEDULER_ARN":"***",
        "S3_BUCKET_IMAGES_NAME":"***",
        "S3_BUCKET_CHAT_PERSISTENCE_NAME":"***",
        "SQS_QUEUE_EVENTS_ARN":"***",
        "SQS_QUEUE_TELEGRAM_UPDATES_NAME":"TelegramUpdates",
        "TELEGRAM_ALLOW_CHAT_IDS":"/telegram/allow-chat-ids",
        "TELEGRAM_BOT_KEY":"/telegram/bot-token"
    }
}
```
and remove the webhook setting from Telegram always via API
```bash
curl --location 'https://api.telegram.org/{{bot-token}}/setWebhook' \
--data '{"url": ""}'
```