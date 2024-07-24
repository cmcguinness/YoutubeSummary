# YouTube Summarizer

Ever get tired of watching long YouTube videos? Wish they'd just get to the point?

Yeah, me too.

So I wrote this app to demonstrate how AI can "solve" this problem for me.  It will take a transcript from a video and ask AI to summarize it to whatever length I choose.

It uses one of two LLMs for this:
* [Deep Infra](https://deepinfra.com)'s version of Llama 3.1 8B
* [OpenAI](https://openai.com)'s gpt-4o-mini

Before you run it, set one of these two environment variables:
* DI_API_KEY
* OPENAI_API_KEY

The first is the API key you have for Deep Infra.  The second is your API key for OpenAI.  Whichever one you supply, that's the service and mode the app will use.

## Caveats

* It uses a python library called `youtube-transcript-api` to retrieve the transcript.  It works, but it's clearly not using documented interfaces.  So don't be surprised if it gets broken at some point.
* There's not a lot of error checking in the code, feel free to improve it!

## Authentication
By default, the user id and password are both `admin`.

But if you specify an environment variable USERDB and set it to something like "{ "bob": "pass1", "tom": "pass2" }", then it will use that as the user database and the default admin/admin will not work.

The login screen is there so that I can put the app up on [railway.app](railway.app) and not have to have it running on my system.  It's a really crappy authentication system.  Feel free to improve it too!



This is a sample program that demonstrates how to generate summaries of the transcripts from YouTube 