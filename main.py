from cmd import PROMPT
from curses import nonl
import re
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp
import hmac
import base64
import time
import requests
from datetime import datetime
import hashlib
import uuid
class text2imgConfig:
    def __init__(self,width=512,height=512,steps=28,mgType=None,modelId=None,sd_loraModelId=None,sd_loraWeight=1,flux_loraModelId=None,flux_loraWeight=1,message_str=None,isS=False,isF=False):
        self.width = width
        self.height = height
        self.steps = steps
        self.mgType = mgType
        self.modelId = modelId
        self.sd_loraModelId = sd_loraModelId
        self.sd_loraWeight = sd_loraWeight
        self.flux_loraModelId = flux_loraModelId
        self.flux_loraWeight = flux_loraWeight
        self.message_str = message_str
        self.isSdLora = isS
        self.isFluxLora = isF

@register("liblibApi", "machinad", "一个强大的AI文生图插件，基于LiblibAI的API服务，支持多种绘图模式和自定义模型配置。可自定义大模型和lora模型- 支持中英文提示词（中文会自动翻译为英文提示词）- 灵活的参数配置- 支持自定义工作流", "1.0.4")
class MyPlugin(Star):
    def __init__(self, context: Context, config: dict, interval=5):
        self.ak = config.get("AccessKey")#获取ak
        self.sk = config.get("SecretKey")#获取sk
        self.width= config.get("width")#获取宽度
        self.height = config.get("height")#获取高度
        self.steps = int(config.get("num_inference_steps"))#获取步数
        self.imgType = config.get("text_imgType")#获取图片类型
        self.modelId = config.get("modelId")#获取模型id
        self.sd_loraModelId = config.get("sd_lora_modelid")#获取模型id
        self.sd_loraWeight = config.get("sd_lora_scale")#获取权重
        self.flux_loraModelId = config.get("flux_lora_modelid")#获取模型id
        self.flux_loraWeight = config.get("flux_lora_scale")#获取权重
        self.isSdLora = config.get("is_SdLora")#获取是否使用lora
        self.isFluxLora = config.get("is_fluxLora")#获取是否使用lora
        self.time_stamp = int(datetime.now().timestamp() * 1000)#获取当前时间戳
        self.signature_nonce = uuid.uuid1()#获取uuid
        self.signature_img = self._hash_sk(self.sk, self.time_stamp, self.signature_nonce)#获取签名
        self.singature_confyui = self._hash_confyui(self.sk, self.time_stamp, self.signature_nonce)#获取签名,confyui专用
        self.signature_ultra_img = self._hash_ultra_sk(self.sk, self.time_stamp, self.signature_nonce)#获取签名,暂时无用，请忽略
        self.signature_status = self._hash_sk_status(self.sk, self.time_stamp, self.signature_nonce)#获取签名,用于获取状态
        self.interval = interval
        self.headers = {'Content-Type': 'application/json'}
        self.text2img_url = self.get_image_url(self.ak, self.signature_img, self.time_stamp,self.signature_nonce)#获取url
        self.confyui_url = self.get_confyui_url(self.ak, self.singature_confyui, self.time_stamp,self.signature_nonce)
        self.text2img_ultra_url = self.get_ultra_image_url(self.ak, self.signature_ultra_img, self.time_stamp,self.signature_nonce)
        self.generate_url = self.get_generate_url(self.ak, self.signature_status, self.time_stamp,self.signature_nonce)
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
                    "seed": -1,
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
                    }
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
                    "seed": -1,
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
        if self.has_chinese(config.message_str):
            logger.info("检测到中文，开始翻译提示词")
            textA = self.exextract_letters(config.message_str)
            llm_pormpt = text2imgConfig(
                message_str = config.message_str,
            )
            sysPormpt = """
                stableDiffusion是一款利用深度学习的文生图模型，支持通过使用提示词来产生新的图像，描述要包含或省略的元素。我在这里引入StableDiffusion算法中的Prompt概念，又被称为提示符。
下面的prompt是用来指导AI绘画模型创作图像的。它们包含了图像的各种细节，如人物的外观、背景、颜色和光线效果，以及图像的主题和风格。这些prompt的格式经常包含括号内的加权数字，用于指定某些细节的重要性或强调。例如，"(masterpiece:1.5)"表示作品质量是非常重要的，多个括号也有类似作用。此外，如果使用中括号，如"{blue hair:white hair:0.3}"，这代表将蓝发和白发加以融合，蓝发占比为0.3。
以下是用prompt帮助AI模型生成图像的例子:(bestquality),highlydetailed,ultra-detailed,cold,solo,(1girl),(detailedeyes),(shinegoldeneyes),(longliverhair),expressionless,(long sleeves),(puffy sleeves),(white wings),shinehalo,(heavymetal:1.2),(metaljewelry),cross-lacedfootwear (chain),(Whitedoves:1.2)
对于结果，请直接输出提示词
                """
            textB = await self.LLMmessage(llm_pormpt,sysPormpt)
            uPrompt = textA + textB
            logger.info("翻译完成，翻译结果为："+str(uPrompt))
        if not config.mgType:
            logger.info("生图类型为空")
            return {"code": 1, "msg": "类型为空，未设置类型"}
        if config.mgType == "sd1.5/XL模式(可自定义模型)":
            logger.info("当前生图类型为"+str(config.mgType))
            base_json = model[config.mgType]
            if not config.isSdLora:
                logger.info("未开启lora模型，移除lora")
                del base_json["generateParams"]["additionalNetwork"]
            return self.run(base_json, self.text2img_url)
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
                    logger.erro(f"lora字段删除错误：{e}")
                    return {"code": 1, "msg": "flux模式调用文生图接口失败，原因：字段删除错误"}
            
            try:
                return self.run(base_json, self.text2img_url)
            except Exception as e:
                logger.erro(f"flux模式调用文生图请求失败，原因：{e}")
                return {"code": 1, "msg": "flux模式调用文生图接口失败，原因：请求失败"}

        elif config.mgType == "confyui模式":
            logger.info("当前生图类型为"+str(config.mgType))
            base_json = model[config.mgType]
            return self.run(base_json, self.confyui_url)
        else:
            logger.info("图片类型错误，或者数值超出大小")
            return {"code": 2, "msg": "设置图片类型错误"}
    def exextract_letters(self,text):
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
        Context = []
        llm_response = await self.context.get_using_provider().text_chat(
        prompt=Prompt,
        session_id=None, # 此已经被废弃
        contexts=Context, # 也可以用上面获得的用户当前的对话记录 context
        image_urls=[], # 图片链接，支持路径和网络链接
        system_prompt=sysPrompt  # 系统提示，可以不传
    )
        return llm_response.result_chain.chain[0].text
    def run(self, data, url, timeout=120):
        """
        发送任务到生图接口，直到返回image为止，失败抛出异常信息
        """
        start_time = time.time()  # 记录开始时间
        # 这里提交任务，校验是否提交成功，并且获取任务ID
        response = requests.post(url=url, headers=self.headers, json=data)# 发送请求
        response.raise_for_status()# 检查响应是否成功
        progress = response.json()# 获取响应数据
        if progress['code'] == 0:
            # 如果获取到任务ID，执行等待生图
            while True:
                current_time = time.time()
                if (current_time - start_time) > timeout:
                    logger.info(f"{timeout}任务超时，已退出轮询。")
                    return None

                generate_uuid = progress["data"]['generateUuid']# 获取任务ID
                data = {"generateUuid": generate_uuid}# 构造请求数据
                response = requests.post(url=self.generate_url, headers=self.headers, json=data)# 发送请求
                response.raise_for_status()# 检查响应是否成功
                progress = response.json()# 获取响应数据

                if progress['data'].get('images') and any(image for image in progress['data']['images'] if image is not None):
                    logger.info(f"任务完成，获取到图像数据。")
                    return progress
                time.sleep(self.interval)
        else:
            return f'任务失败,原因：code {progress["msg"]}'
    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
    @filter.command("ltest")
    async def ltest(self, event: AstrMessageEvent):
        """
        测试保留指令，也可以这这个指令翻译提示词
        """
        message_str = event.message_str
        parts = message_str.split(" ",1)
        prompt = parts[1].strip() if len(parts) > 1 else ""# 获取用户发送的消息
        textImgageConfig = text2imgConfig(
            width = self.width,
            height = self.height,
            steps = self.steps,
            mgType = str(self.imgType),
            modelId = self.modelId,
            sd_loraModelId = self.sd_loraModelId,
            sd_loraWeight = self.sd_loraWeight,
            flux_loraModelId = self.flux_loraModelId,
            flux_loraWeight = self.flux_loraWeight,
            message_str = prompt,
            isS = self.isSdLora,
            isF = self.isFluxLora
        )# 构造请求数据
        Progess = await self.text2img(textImgageConfig)
        yield event.plain_result(str(Progess))
    @filter.command("limg")
    async def limg(self, event: AstrMessageEvent):
        """
        使用文生图，比如/limg 1girl或是/limg 一个男孩，穿红色衣服
        """
        #user_name = event.get_sender_name()# 发送消息的用户昵称
        #yield event.plain_result(f"开始生成图片，当前类型为："+self.imgType)
        message_str = event.message_str # 用户发的纯文本消息字符串
        #yield event.plain_result(f"获取用户原始数据")
        parts = message_str.split(" ",1)
        prompt = parts[1].strip() if len(parts) > 1 else ""# 获取用户发送的消息
        #yield event.plain_result(f"提取提示词"+prompt)
        textImgageConfig = text2imgConfig(
            width = self.width,
            height = self.height,
            steps = self.steps,
            mgType = str(self.imgType),
            modelId = self.modelId,
            sd_loraModelId = self.sd_loraModelId,
            sd_loraWeight = self.sd_loraWeight,
            flux_loraModelId = self.flux_loraModelId,
            flux_loraWeight = self.flux_loraWeight,
            message_str = prompt,
            isS = self.isSdLora,
            isF = self.isFluxLora
        )# 构造请求数据
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
