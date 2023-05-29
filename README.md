# riva-gpt
# How to change the code?

- **Step 1.** 1.	How can we get the returned information from the responses of the microphone?


```python
'''
Open the mic stream as an iterato and then iterating over each response in 
asr_service.streaming_response_generator()
Use is_final to determine whether to finish a sentence

'''
with riva.client.audio_io.MicrophoneStream(
                    args.sample_rate_hz,
                    args.file_streaming_chunk,
                    device=args.input_device,
            ) as stream:
                for response in asr_service.streaming_response_generator(
                        audio_chunks=stream,
                        streaming_config=config,
                ):
                    for result in response.results:
                        if result.is_final:
                            transcripts = result.alternatives[0].transcript  # print(output)
                            output = transcripts

```

- **Step 2.** 1. How can we use the openai api?

```python
'''First,we applied for an api key on openai's website,then we call openai.ChatCompletion.create()
The main input is the messages parameter. Messages must be an array of message objects, where each object has a role (either "system", "user", or "assistant") and content (the content of the message). Conversations can be as short as 1 message or fill many pages.
Assistant -assistant: Messages help to store previous replies. This is to sustain the conversation and provide context for the conversation
You can refer to (https://platform.openai.com/docs/api-reference/chat) for more details
'''
openai.api_key = "openai-api-key"#using you openai key here
model_engine = "gpt-3.5-turbo"
ans = openai.ChatCompletion.create(
      model=model_engine,
      messages=[{"role": "user", "content": "you question"},
                {"role": "assistant", "content": "The answer to the previous question "}]#use "assistant" to maintain context
  )

```
- **Step 3.** 1.	How do we turn text into speech output?
```python
'''Setting the parameters (sample_rate_hz and output_device)'''
    args1 = argparse.Namespace()
    args1.language_code = 'en-US'
    args1.sample_rate_hz = 48000 ##You can check the sample-rate of your own device to replace it 
    args1.stream = True #this shoule be true
    args1.output_device = 24 #You can check the port number of your own device to replace it 
    service = riva.client.SpeechSynthesisService(auth)#This code is request the Riva server to synthesize the language
    nchannels = 1
    sampwidth = 2
    sound_stream = None

'''We call riva.client.audio_io.SoundCallBack() function to create a sound
 stream,then call service.synthesize_online() to syntheric voice.'''
    try:
        if args1.output_device is not None:
            #For playing audio during synthesis you will need to pass audio chunks to riva.client.audio_io.SoundCallBack as they arrive.
            sound_stream = riva.client.audio_io.SoundCallBack(
                args1.output_device, nchannels=nchannels, sampwidth=sampwidth,
                framerate=args1.sample_rate_hz
            )
        if args1.stream:
            #responses1 is the speech returned after synthesis,returning as an iterator
            responses1 = service.synthesize_online(
                answer, None, args1.language_code, sample_rate_hz=args1.sample_rate_hz
            )
            #Playing speech iteratively
            for resp in responses1:    
                if sound_stream is not None:
                    sound_stream(resp.audio)
    finally:
        if sound_stream is not None:
            sound_stream.close()

```
- **Step 4.** 1.	How to set wake words and sleep words?

```python
'''You can modify this part of the code to set your own wake-up word'''
if output == "hello ":#You can specify your wake-up word here,and remember to add a space after it
    is_wakeup = True
    anSwer('here', auth)
    output = ""
if output == "stop " and is_wakeup == True: #You can specify your pause word here,and remember to add a space after it
    is_wakeup = False
    anSwer('Bye! Have a great day!', auth) 
    output = ""
