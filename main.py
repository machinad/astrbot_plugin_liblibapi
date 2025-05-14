from cmd import PROMPT
from curses import nonl
from math import fabs
import os
from pathlib import Path
import re
import httpx
import ssl
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp
import hmac
import base64
import time
import json
import requests
from datetime import datetime
import hashlib
import uuid
class text2imgConfig:
    def __init__(self,
    width=512,
    height=512,
    steps=28,
    seed=-1,
    mgType=None,
    modelId=None,
    sd_loraModelId=None,
    sd_loraWeight=1,
    flux_loraModelId=None,
    flux_loraWeight=1,
    message_str=None,
    isS=False,
    isF=False,
    confyui_api=None,
    istranslate=True,
    translateType=None,
    img_url=None
    ):
        self.width = width
        self.height = height
        self.steps = steps
        self.seed = seed
        self.mgType = mgType
        self.modelId = modelId
        self.sd_loraModelId = sd_loraModelId
        self.sd_loraWeight = sd_loraWeight
        self.flux_loraModelId = flux_loraModelId
        self.flux_loraWeight = flux_loraWeight
        self.message_str = message_str
        self.isSdLora = isS
        self.isFluxLora = isF
        self.confyui_api = confyui_api
        self.istranslate = istranslate
        self.translateType = translateType
        self.img_url = img_url

@register("liblibApi", "machinad", "调用liblib进行文生图、图生图、可以自己换大模型,lora模型，支持contorlnet控制，支持自定义confyuiAPI", "1.0.7")
class MyPlugin(Star):
    def __init__(self, context: Context, config: dict, interval=5):
        self.ak = config.get("AccessKey")#获取ak
        self.sk = config.get("SecretKey")#获取sk
        self.width= config.get("width")#获取宽度
        self.height = config.get("height")#获取高度
        self.steps = int(config.get("num_inference_steps"))#获取步数
        self.seed = config.get("seed")#获取种子
        self.imgType = config.get("text_imgType")#获取图片类型
        self.modelId = config.get("sd1.5/xl_config").get("modelId")#获取模型id
        self.sd_loraModelId = config.get("sd1.5/xl_config").get("sd_lora_modelid")#获取模型id
        self.sd_loraWeight = config.get("sd1.5/xl_config").get("sd_lora_scale")#获取权重
        self.flux_loraModelId = config.get("flux_config").get("flux_lora_modelid")#获取模型id
        self.flux_loraWeight = config.get("flux_config").get("flux_lora_scale")#获取权重
        self.isSdLora = config.get("sd1.5/xl_config").get("is_SdLora")#获取是否使用lora
        self.isFluxLora = config.get("flux_config").get("is_fluxLora")#获取是否使用lora
        self.confyui_api = config.get("confyui_overwriting")#获取confyui api
        self.istranslate = config.get("prompt_Translation").get("is_Translation")#获取是否翻译
        self.translateType = config.get("prompt_Translation").get("Translation_Type")#获取翻译类型
        self.time_stamp = int(datetime.now().timestamp() * 1000)#获取当前时间戳
        self.signature_nonce = uuid.uuid1()#获取uuid
        self.signature_img = self._hash_sk(self.sk, self.time_stamp, self.signature_nonce)#获取签名
        self.singature_confyui = self._hash_confyui(self.sk, self.time_stamp, self.signature_nonce)#获取签名,confyui专用
        self.signature_img_post = self._has_sk_imgPost(self.sk, self.time_stamp, self.signature_nonce)#获取图片上传签名
        self.signature_ultra_img = self._hash_ultra_sk(self.sk, self.time_stamp, self.signature_nonce)#获取签名,暂时无用，请忽略
        self.signature_status = self._hash_sk_status(self.sk, self.time_stamp, self.signature_nonce)#获取签名,用于获取状态
        self.signature_getVersion = self._has_sk_getVersion(self.sk, self.time_stamp, self.signature_nonce)#获取签名,用于获取版本
        self.interval = interval
        self.headers = {'Content-Type': 'application/json'}
        self.text2img_url = self.get_image_url(self.ak, self.signature_img, self.time_stamp,self.signature_nonce)#获取文生图url
        self.confyui_url = self.get_confyui_url(self.ak, self.singature_confyui, self.time_stamp,self.signature_nonce)#confyui模式的url
        self.text2img_ultra_url = self.get_ultra_image_url(self.ak, self.signature_ultra_img, self.time_stamp,self.signature_nonce)#无用的url
        self.generate_url = self.get_generate_url(self.ak, self.signature_status, self.time_stamp,self.signature_nonce)#获取状态url
        self.imgPost_url = self.get_imgPost_url(self.ak, self.signature_img_post, self.time_stamp,self.signature_nonce)#图片上传url
        self.getVersion_url = self.get_getVersion_url(self.ak, self.signature_getVersion, self.time_stamp,self.signature_nonce)#获取版本url
        self.path = Path("./data/plugins_data/liblib")
        super().__init__(context)
    def hmac_sha1(self, key, code):#加密
        hmac_code = hmac.new(key.encode(), code.encode(), hashlib.sha1)
        return hmac_code.digest()
    def _hash_sk(self, key, s_time, ro):
        """加密sk"""
        data = "/api/generate/webui/text2img" + "&" + str(s_time) + "&" + str(ro)
        s = base64.urlsafe_b64encode(self.hmac_sha1(key, data)).rstrip(b'=').decode()
        return s
    def _hash_confyui(self,key,s_time,ro):
        """加密sk"""
        data = "/api/generate/comfyui/app" + "&" + str(s_time) + "&" + str(ro)
        s = base64.urlsafe_b64encode(self.hmac_sha1(key, data)).rstrip(b'=').decode()
        return s
    def _hash_ultra_sk(self, key, s_time, ro):
        """加密sk"""
        data = "/api/generate/webui/text2img/ultra" + "&" + str(s_time) + "&" + str(ro)
        s = base64.urlsafe_b64encode(self.hmac_sha1(key, data)).rstrip(b'=').decode()
        return s

    def _hash_sk_status(self, key, s_time, ro):
        """加密sk"""
        data = "/api/generate/webui/status" + "&" + str(s_time) + "&" + str(ro)
        s = base64.urlsafe_b64encode(self.hmac_sha1(key, data)).rstrip(b'=').decode()
        return s
    def _has_sk_imgPost(self,key, s_time, ro):
        """加密sk"""
        data = "/api/generate/upload/signature"+"&"+str(s_time)+"&"+str(ro)
        s = base64.urlsafe_b64encode(self.hmac_sha1(key, data)).rstrip(b'=').decode()
        return s
    def _has_sk_getVersion(self,key, s_time, ro):
        """加密sk"""
        data = "/api/model/version/get"+"&"+str(s_time)+"&"+str(ro)
        s = base64.urlsafe_b64encode(self.hmac_sha1(key, data)).rstrip(b'=').decode()
        return s
    def get_image_url(self, ak, signature, time_stamp, signature_nonce):

        url = f"https://openapi.liblibai.cloud/api/generate/webui/text2img?AccessKey={ak}&Signature={signature}&Timestamp={time_stamp}&SignatureNonce={signature_nonce}"
        return url

    def get_confyui_url(self, ak, signature, time_stamp, signature_nonce):
        url = f"https://openapi.liblibai.cloud/api/generate/comfyui/app?AccessKey={ak}&Signature={signature}&Timestamp={time_stamp}&SignatureNonce={signature_nonce}"
        return url

    def get_ultra_image_url(self, ak, signature, time_stamp, signature_nonce):

        url = f"https://openapi.liblibai.cloud/api/generate/webui/text2img/ultra?AccessKey={ak}&Signature={signature}&Timestamp={time_stamp}&SignatureNonce={signature_nonce}"
        return url

    def get_generate_url(self, ak, signature, time_stamp, signature_nonce):

        url = f"https://openapi.liblibai.cloud/api/generate/webui/status?AccessKey={ak}&Signature={signature}&Timestamp={time_stamp}&SignatureNonce={signature_nonce}"
        return url
    def get_imgPost_url(self,ak,signature,time_stamp,signature_nonce):
        url = f"https://openapi.liblibai.cloud/api/generate/upload/signature?AccessKey={ak}&Signature={signature}&Timestamp={time_stamp}&SignatureNonce={signature_nonce}"
        return url
    def get_getVersion_url(self,ak,signature,time_stamp,signature_nonce):
        url = f"https://openapi.liblibai.cloud/api/model/version/get?AccessKey={ak}&Signature={signature}&Timestamp={time_stamp}&SignatureNonce={signature_nonce}"
        return url
    async def text2img(self, config: text2imgConfig):
        uPrompt = config.message_str
        model = {
            "sd1.5/XL模式(可自定义模型)":{
                "templateUuid": "e10adc3949ba59abbe56e057f20f883e",
                "generateParams":{
                    "checkPointId": config.modelId,
                    "vaeId": "",
                    "prompt":uPrompt,
                    "negativePrompt": "bad-artist, bad-artist-anime, bad-hands-5, bad-image-v2-39000, bad-picture-chill-75v, bad_prompt, bad_prompt_version2, badhandv4, NG_DeepNegative_V1_75T, EasyNegative,2girls, 3girls,,bad quality, poor quality, doll, disfigured, jpg, toy, bad anatomy, missing limbs, missing fingers, 3d, cgi",
                    "clipSkip": 2,
                    "sampler": 15,
                    "steps": config.steps,
                    "cfgScale": 7,
                    "width": config.width,
                    "height": config.height,
                    "imgCount": 1,
                    "randnSource": 0,
                    "seed": config.seed,
                    "restoreFaces": 0,
                    "additionalNetwork":[
                        {
                            "modelId": config.sd_loraModelId,
                            "weight": config.sd_loraWeight
                        }
                    ],
                    "hiResFixInfo":{
                        "hiresSteps": 28,
                        "hiresDenoisingStrength": 0.45,
                        "upscaler": 10,
                        "resizedWidth": config.width*2,
                        "resizedHeight": config.height*2
                    },
                    "controlNet":[
                        {
                            "unitOrder": 1,
                            "sourceImage": "",
                            "width": 1024,
                            "height": 1024,
                            "preprocessor": 2,
                            "annotationParameters":{
                                "depthMidas":{
                                    "preprocessorResolution": 512
                                }
                            },
                            "model": "cf63d214734760dcdc108b1bd094921b",
                            "controlWeight": 1, 
                            "startingControlStep": 0,
                            "endingControlStep": 1,
                            "pixelPerfect": 1,
                            "controlMode": 0,
                            "resizeMode": 0,
                            "maskImage": ""
                        }
                    ]
                }
            },
            "flux模式":{
                "templateUuid": "6f7c4652458d4802969f8d089cf5b91f",
                "generateParams":{
                    "prompt": uPrompt,
                    "steps": config.steps,
                    "width": config.width,
                    "height": config.height,
                    "imgCount": 1,
                    "seed": config.seed,
                    "restoreFaces": 0,
                    "additionalNetwork":[
                        {
                            "modelId": config.flux_loraModelId,
                            "weight": config.flux_loraWeight
                        }
                    ]
                }
            },
            "confyui模式":{
                "templateUuid": "4df2efa0f18d46dc9758803e478eb51c",
                "generateParams": {
                "5": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {
                        "width": config.width,
                        "height": config.height,
                        "batch_size": 1
                    }
                },
                "10": {
                    "class_type": "UNETLoader",
                    "inputs": {
                        "unet_name": "412b427ddb674b4dbab9e5abd5ae6057",
                        "weight_dtype": "fp8_e4m3fn"
                    }
                
                },
                "11": {
                    "class_type": "DualCLIPLoader",
                    "inputs": {
                        "clip_name1": "clip_l",
                        "clip_name2": "t5xxl_fp8_e4m3fn",
                        "type": "flux",
                        "device": "default"
                    }
                
                },
                "13": {
                    "class_type": "LoraLoader",
                    "inputs": {
                        "lora_name": "92b126744e7b49dfb76202b094d406e9",
                        "strength_model": 0.6,
                        "strength_clip": 2
                    }
                },
                "15": {
                    "class_type": "CLIPTextEncodeFlux",
                    "inputs": {
                        "clip_l": "",
                    "t5xxl": uPrompt,
                    "guidance": 3.5
                    }
                
                 },
                "16": {
                    "class_type": "VAELoader",
                    "inputs": {
                        "vae_name": "ae.sft"
                    }
                
                 },
                "17": {
                    "class_type": "FluxSamplerParams+",
                    "inputs": {
                        "seed": "49375",
                        "sampler": "euler",
                        "scheduler": "simple",
                        "steps": "15",
                        "guidance": "3.5",
                        "max_shift": "",
                        "base_shift": "",
                        "denoise": ""
                    }
                },
                "19": {
                    "class_type": "LoraLoader",
                    "inputs": {
                        "lora_name": "60cdd0badb844e039aa3cf0d9908f70e",
                        "strength_model": 0.6,
                        "strength_clip": 2
                    }
                },
                "workflowUuid": "f454f4a44bc440ca9427ca48c931598e"
                }
            }
        }
        if self.has_chinese(config.message_str) and config.istranslate:
            logger.info("检测到中文，开始翻译提示词")
            if config.translateType == "sd格式提示词":
                sysPormpt = """
                stableDiffusion是一款利用深度学习的文生图模型，支持通过使用提示词来产生新的图像，描述要包含或省略的元素。我在这里引入StableDiffusion算法中的Prompt概念，又被称为提示符。
下面的prompt是用来指导AI绘画模型创作图像的。它们包含了图像的各种细节，如人物的外观、背景、颜色和光线效果，以及图像的主题和风格。这些prompt的格式经常包含括号内的加权数字，用于指定某些细节的重要性或强调。例如，"(masterpiece:1.5)"表示作品质量是非常重要的，多个括号也有类似作用。此外，如果使用中括号，如"{blue hair:white hair:0.3}"，这代表将蓝发和白发加以融合，蓝发占比为0.3。
以下是用prompt帮助AI模型生成图像的例子:(bestquality),highlydetailed,ultra-detailed,cold,solo,(1girl),(detailedeyes),(shinegoldeneyes),(longliverhair),expressionless,(long sleeves),(puffy sleeves),(white wings),shinehalo,(heavymetal:1.2),(metaljewelry),cross-lacedfootwear (chain),(Whitedoves:1.2)
对于结果，请直接输出提示词
                """
                logger.info("使用sd格式提示词")
            elif config.translateType == "英语直译(自然语言)":
                sysPormpt = """
                你是一个好用的翻译助手。请将我的中文翻译成英文，将所有非中文的翻译成中文。我发给你所有的话都是需要翻译的内容，你只需要回答翻译结果。翻译结果请符合中文的语言习惯。
                """
                logger.info("仅翻译成英语")
            elif config.translateType == "中译中(ai润色)":
                sysPormpt = """请对文字润色，润色结果请符合中文的语境习惯。请直接输出润色后的文字"""
                logger.info("不翻译，仅润色")
            textA = await self.exextract_letters(config.message_str)#提取可能存在的lora提示词
            llm_pormpt = text2imgConfig(
                message_str = config.message_str,
            )#获取一个新的用户消息实例
            
            textB = await self.LLMmessage(llm_pormpt,sysPormpt)#获取翻译结果
            uPrompt = textA + textB#拼接翻译结果
            logger.info("翻译完成，翻译结果为："+str(uPrompt))


        if not config.mgType:
            logger.info("生图类型为空")
            return {"code": 1, "msg": "生图模式类型为空，未设置类型"}
        if config.mgType == "sd1.5/XL模式(可自定义模型)":
            logger.info("当前生图类型为"+str(config.mgType))
            base_json = model[config.mgType]
            if config.img_url != None:
                image_name = "image"+str(uuid.uuid1())
                image_file = image_name+"."+"png"
                image_bt = await self.download_image(config.img_url)
                progress = await self.signature_image(self.imgPost_url,image_name)
                if progress.get("code") == 0:
                    logger.info("图片上传请求发起成功，回调参数为："+str(progress))
                    base_json["generateParams"]["controlNet"][0]["sourceImage"] = await self.upload_image(progress,image_file,image_bt)
            else:
                logger.info("未传入图片，移除controlnet")
                del base_json["generateParams"]["controlNet"]
            if not config.isSdLora:
                logger.info("未开启lora模型，移除lora")
                del base_json["generateParams"]["additionalNetwork"]
            logger.info("调用文生图接口:请求体为："+str(base_json))
            

            return await self.run(base_json, self.text2img_url)


        elif config.mgType == "flux模式":
            logger.info("当前生图类型为"+str(config.mgType))
            try:
                base_json = model[config.mgType]
            except Exception as e:
                logger.erro(f"flux模式调用文生图接口失败，原因：json类型设置错误{e}")
                return {"code": 1, "msg": "flux模式调用文生图接口失败，原因：json类型设置错误"}

            if not config.isFluxLora:
                logger.info("未开启lora模型,移除lora")
                try:
                    del base_json["generateParams"]["additionalNetwork"]
                except Exception as e:
                    logger.info(f"lora字段删除错误：{e}")
                    return {"code": 1, "msg": "flux模式调用文生图接口失败，原因：字段删除错误"}
            
            try:
                return await self.run(base_json, self.text2img_url)
            except Exception as e:
                logger.info(f"flux模式调用文生图请求失败，原因：{e}")
                return {"code": 1, "msg": "flux模式调用文生图接口失败，原因：请求失败"}

        elif config.mgType == "confyui模式":
            if config.confyui_api is not None and config.confyui_api != "":
                api_str = config.confyui_api.replace("{{prompt}}", uPrompt)
                api_str = config.confyui_api.replace("{{height}}", config.height)
                api_str = config.confyui_api.replace("{{width}}", config.width)
                api_str = config.confyui_api.replace("{{steps}}", config.steps)
                api_str = config.confyui_api.replace("{{seed}}", config.seed)
                api_str = config.confyui_api.replace("{{img_url}}", config.img_url)
                try:
                    base_json = json.loads(api_str)
                except Exception as e:
                    logger.info(f"confyui模式调用文生图接口失败，原因：json类型设置错误{e}")
                    logger.info(str(api_str))
                    return {"code": 1, "msg": "confyui模式调用文生图接口失败，原因：json类型设置错误"}
                logger.info("载入自定义confyui接口")
            else:
                base_json = model[config.mgType]
            logger.info("当前生图类型为"+str(config.mgType))
            return await self.run(base_json, self.confyui_url)
        else:
            logger.info("图片类型错误，或者数值超出大小")
            return {"code": 2, "msg": "设置图片类型错误"}
    async def exextract_letters(self,text):
        latters = re.findall(r'[a-zA-Z]', text)
        return " ".join(latters)
    def has_chinese(self,text):
        """
        检查字符串中是否包含中文字符
        """
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False
    async def LLMmessage(self,event:text2imgConfig,sysPrompt):
        """
        调用LLM翻译提示词
        """
        Prompt = event.message_str
        Context = [
            Comp.Plain(f"图片已经生成，消耗点数：{pointsCost}，账户余额：{accountBalance}")
        ]
        llm_response = await self.context.get_using_provider().text_chat(
        prompt=Prompt,
        session_id=None, # 此已经被废弃
        contexts=Context, # 也可以用上面获得的用户当前的对话记录 context
        image_urls=[], # 图片链接，支持路径和网络链接
        system_prompt=sysPrompt  # 系统提示，可以不传
    )
        return llm_response.result_chain.chain[0].text
    async def run(self, data, url, timeout=120):
        """
        发送任务到生图接口，直到返回image为止，失败抛出异常信息
        """
        start_time = time.time()  # 记录开始时间
        # 这里提交任务，校验是否提交成功，并且获取任务ID
        async with httpx.AsyncClient() as client:
            response = await client.post(url=url, headers=self.headers, json=data)
            response.raise_for_status()
            progress = response.json()# 获取响应数据
            if progress["code"]==0:
                while True:
                    current_time = time.time()
                    if(current_time - start_time)>timeout:
                        logger.info(f"在发起生图任务后{current_time-start_time}秒，未获取到任务ID，已退出轮询。")
                        return {"code": 1, "msg": "任务已经超时，文生图失败"}
                    generate_uuid = progress["data"]['generateUuid']# 获取任务ID
                    data = {"generateUuid":generate_uuid}# 装载任务ID
                    response = await client.post(url=self.generate_url, headers=self.headers, json=data)# 根据已创建的任务id发送请求，进行任务状态查询
                    response.raise_for_status()# 检查响应是否成功
                    progress = response.json()# 获取响应数据
                    if progress['data'].get('images') and any(image for image in progress['data']['images'] if image is not None):
                        logger.info("图片生成完成")
                        return progress
                    time.sleep(self.interval)# 等待一段时间后再次轮询
            else:
                return {"code": {progress["code"]}, "msg": {progress["msg"]}}
    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
    @filter.command("lcha")
    async def lcha(self, event: AstrMessageEvent):
        """
        模型参数查询命令格式为/lcha f454f4a44bc440ca9427ca48c931598e
        """
        message = event.message_obj.message
        message_str = self.textFilter(message)
        parts = str(message_str).split(" ",1)
        prompt = parts[1].strip() if len(parts) > 1 else ""# 获取用户发送的消息
        data = {
            "versionUuid": str(prompt),
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url=self.getVersion_url, headers=self.headers, json=data)
            response.raise_for_status()
            progress = response.json()
            logger.info("模型查询参数为"+str(progress))
            yield event.plain_result(
                f"已经查询到模型信息：\n"
                f"模型ID：{progress.get('data', {}).get('versionUuid')}\n"
                f"模型名称：{progress.get('data', {}).get('modelName')}\n"
                f"模型版本：{progress.get('data', {}).get('versionName')}\n"
                f"基础算法：{progress.get('data', {}).get('baseAlgoName')}\n"
                )
    def textFilter(self,message:list)->str:
        for msg in message:
            if msg.type == "Plain":
                return msg.text
        return None
    def imageFilter(self,message:list)->str:
        for msg in message:
            if msg.type == "Image":
                return msg.url
        return None
    @filter.command("limg")
    async def limg(self, event: AstrMessageEvent):
        """
        使用文生图，比如/limg 1girl或是/limg 一个男孩，穿红色衣服
        """
        #user_name = event.get_sender_name()# 发送消息的用户昵称
        #yield event.plain_result(f"开始生成图片，当前类型为："+self.imgType)
        #message_str = event.message_str # 用户发的纯文本消息字符串
        message = event.message_obj.message# 用户发的消息对象
        image_url = self.imageFilter(message)
        image_url = image_url.replace("https","http")
        message_str = self.textFilter(message)
        parts = str(message_str).split(" ",1)
        prompt = parts[1].strip() if len(parts) > 1 else ""# 获取用户发送的消息
        textImgageConfig = text2imgConfig(
            width = self.width,
            height = self.height,
            steps = self.steps,
            seed = self.seed,
            mgType = str(self.imgType),
            modelId = self.modelId,
            sd_loraModelId = self.sd_loraModelId,
            sd_loraWeight = self.sd_loraWeight,
            flux_loraModelId = self.flux_loraModelId,
            flux_loraWeight = self.flux_loraWeight,
            message_str = prompt,
            isS = self.isSdLora,
            isF = self.isFluxLora,
            confyui_api = self.confyui_api,
            istranslate=self.istranslate,
            translateType=self.translateType,
            img_url=image_url
        )# 构造请求数据
        #yield event.plain_result(f"获取用户原始数据")
        
        
        #yield event.plain_result(f"提取提示词"+prompt)
       
        #yield event.plain_result(f"配置实例初始化完成")
        try:
            Progess = await self.text2img(textImgageConfig)# 发送请求
        except Exception as e:
            yield event.plain_result(f"调用文生图接口失败，原因：{e}")
            return
        #yield event.plain_result(f"调用文生图接口") 
        #yield event.plain_result("回调参数"+str(Progess))
        logger.info(str(Progess))# 返回原始信息
        code = Progess.get("code",None)# 获取状态码
        msg = Progess.get("msg",None)#获取错误信息
        if code == 0:
            pointsCost = Progess.get("data",{}).get("pointsCost",None)# 获取消耗点数
            accountBalance = Progess.get("data",{}).get("accountBalance",None)# 获取账户余额
            img_url = Progess.get("data",{}).get("images",[{}])[0].get("imageUrl",None)# 获取图片链接
            chain = [
                Comp.At(qq=event.get_sender_id()), # At 消息发送者
                Comp.Plain(f"图片已经生成，消耗点数：{pointsCost}，账户余额：{accountBalance}"), # 发送文本消息
                Comp.Image.fromURL(img_url) # 从 URL 发送图片
            ]
            yield event.chain_result(chain)
            message_chain = event.get_messages()
            logger.info(message_chain)
            return
        else:
            yield event.plain_result(f"图片生成失败，状态码:{code} 原因：{msg}")
            return
    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""


    async def download_image(self, url: str):
        """
        下载图片并返回二进制数据
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
            except Exception as e:
                logger.info(f"图片下载失败，原因：{e}")
                return None
            return response.content

    async def signature_image(self,url:str,name:str):
        """
        图片上传请求发起，获取回调签名参数，用于上传图片
        """
        data = {
            "name": name,
            "extension" : "png"
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=self.headers, json=data)
                response.raise_for_status()
                progress = response.json()
            except Exception as e:
                logger.info(f"图片上传请求发起失败，原因：{e}")
                return None
            return progress

    async def upload_image(self,progress:dict,image_file,save_path:bytes):
        """
        对图片二进制数据进行签名并上传
        """
        async with httpx.AsyncClient() as client:
            data = {
                'key': progress["data"]["key"],
                'policy': progress["data"]["policy"],
                'x-oss-date': progress["data"]["xOssDate"],
                'x-oss-expires': progress["data"]["xOssExpires"],
                'x-oss-signature': progress["data"]["xOssSignature"],
                'x-oss-credential': progress["data"]["xOssCredential"],
                'x-oss-signature-version': progress["data"]["xOssSignatureVersion"],
            }
            files = {
                'file': (image_file, save_path, 'image/png')
            }
            try:
                response = await client.post(progress["data"]["postUrl"],data=data, files=files)
                response.raise_for_status()
                return progress.get("data").get("postUrl")+"/"+progress.get("data").get("key")
            except Exception as e:
                logger.info(f"图片上传失败，原因：{e}")
                return None

    async def get_signature_image_url(self,url:str,post_url):
        """
        该方法用于将消息平台的图片链接转换为liblib的api可以直接调用的图片链接
        该方法会先将图片下载到本地，然后再签名上传到服务器，最后返回图片链接
        """
        image_name = "image"+str(uuid.uuid1())
        image_file = image_name+"."+"png"
        imge_byte = await self.download_image(url)
        if imge_byte is None:
            logger.info("图片二进制数据下载下载失败")
            return None
        progress = await self.signature_image(post_url,image_name)
        if progress is None:
            logger.info("图片上传请求发起失败,未获得签名数据")
            return None
        get_url = await self.upload_image(progress,image_file,imge_byte)
        if get_url is None:
            logger.info("图片上传失败,未能获取到图片链接")
            return None
        return get_url
