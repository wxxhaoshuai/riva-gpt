
import argparse
from typing import List, Iterable
import riva.client.proto.riva_asr_pb2 as rasr
import riva.client
from riva.client.argparse_utils import add_asr_config_argparse_parameters, add_connection_argparse_parameters
import openai
import riva.client.audio_io
import time

#This is the part of typing the command line
#Only the input device and the sampling rate need to be specified
def parse_args() -> argparse.Namespace:
    default_device_info = riva.client.audio_io.get_default_input_device_info()
    default_device_index = None if default_device_info is None else default_device_info['index']
    parser = argparse.ArgumentParser(
        description="Streaming transcription from microphone via Riva AI Services",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input-device", type=int, default=default_device_index, help="An input audio device to use.")
    parser.add_argument("--list-devices", action="store_true", help="List input audio device indices.")
    parser = add_asr_config_argparse_parameters(parser, profanity_filter=True)
    parser = add_connection_argparse_parameters(parser)
    parser.add_argument(
        "--sample-rate-hz",
        type=int,
        help="A number of frames per second in audio streamed from a microphone.",
        default=16000,
    )
    parser.add_argument(
        "--file-streaming-chunk",
        type=int,
        default=1600,
        help="A maximum number of frames in a audio chunk sent to server.",
    )
    args = parser.parse_args()
    return args

#This function is used to make a speech using the microphone. "answer" is the content of the speech, which you can change
#These codes are modified based on riva's tutorials,you can get more details on it on github https://github.com/nvidia-riva/python-clients/tutorials
def anSwer(answer,auth):
    
    args1 = argparse.Namespace()
    args1.language_code = 'en-US'
    args1.output_divece = 24
    args1.sample_rate_hz = 48000
    args1.stream = True
    args1.output_device = 24
    service = riva.client.SpeechSynthesisService(auth)
    nchannels = 1
    sampwidth = 2
    sound_stream = None
    try:
        if args1.output_device is not None:
            #For playing audio during synthesis you will need to pass audio chunks to riva.client.audio_io.SoundCallBack as they arrive.
            sound_stream = riva.client.audio_io.SoundCallBack(
                args1.output_device, nchannels=nchannels, sampwidth=sampwidth,
                framerate=args1.sample_rate_hz
            )
        if args1.stream:
            responses1 = service.synthesize_online(
                answer, None, args1.language_code, sample_rate_hz=args1.sample_rate_hz
            )
            for resp in responses1:    
                if sound_stream is not None:
                    sound_stream(resp.audio)
    finally:
        if sound_stream is not None:
            sound_stream.close()

def main() :
    output = ""  
    answer = ""
    openai.api_key = "openai-api-key"#using you openai key here
    model_engine = "gpt-3.5-turbo"
    
    args = parse_args()
    #the args is used to specifed the speech output
    args1 = argparse.Namespace()
    args1.language_code = 'en-US'
    args1.output_divece = 24
    args1.sample_rate_hz = 48000
    args1.stream = True
    
    if args.list_devices:
        devices = riva.client.audio_io.list_input_devices()
        output += str(devices) + "\n"  
        return output
    auth = riva.client.Auth(args.ssl_cert, args.use_ssl, args.server)
    asr_service = riva.client.ASRService(auth)
    config = riva.client.StreamingRecognitionConfig(
        config=riva.client.RecognitionConfig(
            encoding=riva.client.AudioEncoding.LINEAR_PCM,
            language_code=args.language_code,
            max_alternatives=1,
            profanity_filter=args.profanity_filter,
            enable_automatic_punctuation=args.automatic_punctuation,
            verbatim_transcripts=not args.no_verbatim_transcripts,
            sample_rate_hertz=args.sample_rate_hz,
            audio_channel_count=1,
        ),
        interim_results=True,
    )
    riva.client.add_word_boosting_to_config(config, args.boosted_lm_words, args.boosted_lm_score)
    is_close = False
    is_wakeup = False
    while True:
        #Use iterators to receive mic's stream
        if not is_close:
            with riva.client.audio_io.MicrophoneStream(
                    args.sample_rate_hz,
                    args.file_streaming_chunk,
                    device=args.input_device,
            ) as stream:
                try:
                    for response in asr_service.streaming_response_generator(
                            audio_chunks=stream,
                            streaming_config=config,
                    ):
                        for result in response.results:
                            if result.is_final:
                                transcripts = result.alternatives[0].transcript  # print(output)
                                output = transcripts
                        if  output != '':  
                            if output == "hello ":#You can specify your wake-up word here,and remember to add a space after it
                                is_wakeup = True
                                anSwer('here', auth)
                                output = ""
                            if output == "stop " and is_wakeup == True: #You can specify your pause word here,and remember to add a space after it
                                is_wakeup = False
                                anSwer('Bye! Have a great day!', auth) 
                                output = ""
                            if is_wakeup == True and output != '':
                                print("ask:", output)
                                stream.close()
                                is_close = True
                                ans = openai.ChatCompletion.create(
                                    model=model_engine,
                                    messages=[{"role": "user", "content": output},
                                              {"role": "assistant", "content": answer}]#use "assistant" to maintain context
                                )
                                output = ''
                                answer = ans.choices[0].message["content"]
                                print("AI:", answer)
                                args1.output_device = 24
                                args1.sample_rate_hz = 48000

                                service = riva.client.SpeechSynthesisService(auth)
                                nchannels = 1
                                sampwidth = 2
                                sound_stream = None
                                try:
                                    if args1.output_device is not None:
                                        sound_stream = riva.client.audio_io.SoundCallBack(
                                            args1.output_device, nchannels=nchannels, sampwidth=sampwidth,
                                            framerate=args1.sample_rate_hz
                                        )
                                    start = time.time()
                                    if args1.stream:
                                        responses1 = service.synthesize_online(
                                            answer, None, args1.language_code, sample_rate_hz=args1.sample_rate_hz
                                        )
                                        first = True
                                        #print(responses)
                                        for resp in responses1:
                                            stop = time.time()
                                            if first:
                                                print(f"Time to first audio: {(stop - start):.3f}s")
                                                first = False
                                            if sound_stream is not None:
                                                #print("a:",time.time())
                                                sound_stream(resp.audio)
                                                #print("b:",time.time())
                                                
                                finally:
                                    if sound_stream is not None:
                                        sound_stream.close()
                                        #mic_closed = False
                                        is_close = True
                                break
                            
                finally:
                    is_close = False
        else:
            is_close = False





if __name__ == '__main__':
    main()