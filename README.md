# LudusSMA

## INTRODUCTION
LudusSMA aims to help board game clubs with Instagram. The main goal is to automate the creation of stories to remind followers of events the association is participating in, as well as to manage the association's Instagram account without the need to access Instagram itself.

With the aim of automating the creation of stories, some macro categories of events can be created. The idea in this case is to create formats so that a certain type of event will always have the same background image and have more consistency. For example, you can choose a specific image to be associated with "Bang Tournaments". That way, every time a story is posted to remind followers of the upcoming tournaments, that image will be used as the background. More details about the specific event will be added to the story, including the date, time, and location.

These macro categories are called _Event Types_.

Then the bot user can add events that must belong to some _event_type_. With reference to the previous example, _Bang Tournament_ is the event type, then the _event_ is some Bang Tournament on March 7th, from 14 to 20, in Verona.


Its functionalities include

- Create and manage event categories, such as tournaments or festivals;- Create specific events and Instagram Stories to remind followers of them;
- Create individual posts or stories, complete with images and descriptions.
## ARCHITECTURE

The Whole architecture is based on AWS, in particular:

- Amazon Bedrock: text and image generation models are employed
    - LLama 3.1 model to generate post and story description and to infer from natural Language the specifics of an event type; 
    - Stable Diffusion v1 by StabilityAI to generate images for posts and stories;
- Lambda Functions: Host the backend and the bot code.
    - telegram API to manage the bot on telegram; 
    - Instagram API to publish posts and stories;
- SQS
- S3
- …


## OVERALL BOT STRUCTURE

![Bot Flow](/Documentation/bot_flow.png)