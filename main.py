from curses import nonl
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
@register("liblibApi", "machinad", "一个调取liblib在线工作流进行ai绘图的插件", "1.0.2")
class MyPlugin(Star):
    def __init__(self, context: Context, config: dict, interval=5):
        self.ak = config.get("AccessKey")#获取ak
        self.sk = config.get("SecretKey")#获取sk
        self.width= config.get("width")#获取宽度
        self.height = config.get("height")#获取高度
        self.steps = int(config.get("num_inference_steps"))#获取步数
        self.imgType = config.get("imgType")#获取图片类型
        self.modelId = config.get("modelId")#获取模型id
        self.time_stamp = int(datetime.now().timestamp() * 1000)#获取当前时间戳
        self.signature_nonce = uuid.uuid1()#获取uuid
        self.signature_img = self._hash_sk(self.sk, self.time_stamp, self.signature_nonce)#获取签名
        self.singature_confyui = self._hash_confyui(self.sk, self.time_stamp, self.signature_nonce)#获取签名,confyui专用
        self.signature_ultra_img = self._hash_ultra_sk(self.sk, self.time_stamp, self.signature_nonce)#获取签名,暂时无用，请忽略
        self.signature_status = self._hash_sk_status(self.sk, self.time_stamp, self.signature_nonce)#获取签名,暂时无用，请忽略
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
    def text2img(self, modelId,message_str, width, height,steps):
        ""
        """
        文生图全示例 json
        """
        base_json1 = {
            "templateUuid": "e10adc3949ba59abbe56e057f20f883e",
            "generateParams": {
                "checkPointId": "0ea388c7eb854be3ba3c6f65aac6bfd3",
                "vaeId": "",
                "prompt": message_str,
                "negativePrompt": "bad-artist, bad-artist-anime, bad-hands-5, bad-image-v2-39000, bad-picture-chill-75v, bad_prompt, bad_prompt_version2, badhandv4, NG_DeepNegative_V1_75T, EasyNegative,2girls, 3girls,,bad quality, poor quality, doll, disfigured, jpg, toy, bad anatomy, missing limbs, missing fingers, 3d, cgi",
                "width": width,
                "height": height,
                "imgCount": 1,
                "cfgScale": 7,
                "randnSource": 0,
                "seed": -1,
                "clipSkip": 2,
                "sampler": 15,
                "steps": steps,
                "restoreFaces": 0,
                "additionalNetwork": [
                    {
                        "modelId": "3dc63c4fe3df4147ac8a875db3621e9f",
                        "weight": 0.6
                    }
                ],
                "hiResFixInfo": {
                    "hiresDenoisingStrength": 0.45,
                    "hiresSteps": 28,
                    "resizedHeight": height*2,
                    "resizedWidth": width*2,
                    "upscaler": 10
                },
            }
        }
        model = {
            "0":{
                "templateUuid": "e10adc3949ba59abbe56e057f20f883e",
                "generateParams":{
                    "checkPointId": modelId,
                    "vaeId": "",
                    "prompt":message_str,
                    "negativePrompt": "bad-artist, bad-artist-anime, bad-hands-5, bad-image-v2-39000, bad-picture-chill-75v, bad_prompt, bad_prompt_version2, badhandv4, NG_DeepNegative_V1_75T, EasyNegative,2girls, 3girls,,bad quality, poor quality, doll, disfigured, jpg, toy, bad anatomy, missing limbs, missing fingers, 3d, cgi",
                    "clipSkip": 2,
                    "sampler": 15,
                    "steps": steps,
                    "cfgScale": 7,
                    "width": width,
                    "height": height,
                    "imgCount": 1,
                    "randnSource": 0,
                    "seed": -1,
                    "restoreFaces": 0,
                    "additionalNetwork":[
                        {
                            "modelId": "31360f2f031b4ff6b589412a52713fcf",
                            "weight": 0.6
                        }
                    ],
                    "hiResFixInfo":{
                        "hiresSteps": 28,
                        "hiresDenoisingStrength": 0.45,
                        "upscaler": 10,
                        "resizedWidth": width*2,
                        "resizedHeight": height*2
                    }
                }
            },
            "1":{
                "templateUuid": "6f7c4652458d4802969f8d089cf5b91f",
                "generateParams":{
                    "prompt": message_str,
                    "steps": steps,
                    "width": width,
                    "height": height,
                    "imgCount": 1,
                    "seed": -1,
                    "restoreFaces": 0,
                    "additionalNetwork":[
                        {
                            "modelId": "169505112cee468b95d5e4a5db0e5669",
                            "weight": 1.0
                        }
                    ]
                }
            },
            "2":{
                "templateUuid": "4df2efa0f18d46dc9758803e478eb51c",
                "generateParams": {
                "5": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {
                        "width": width,
                        "height": height,
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
                    "t5xxl": message_str,
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
        if not self.imgType:
            logger.info("未设置图片类型，使用默认类型")
            return 
        else:
            if self.imgType == 0 or self.imgType == 1:
                logger.info("当前生图类型为{imgType},使用sd1.5/xl模式")
                base_json = model[str(self.imgType)]
                return self.run(base_json, self.text2img_url)
            elif self.imgType == 2:
                logger.info("当前生图类型为{imgType},使用confyui模式")
                base_json = model[str(self.imgType)]
                return self.run(base_json, self.confyui_url)
            else:
                logger.info("图片类型错误，或者数值超出大小")
                return
        base_json = model[str(self.imgType)]
        return self.run(base_json, self.text2img_url)
    def run(self, data, url, timeout=120):
        """
        发送任务到生图接口，直到返回image为止，失败抛出异常信息
        """
        start_time = time.time()  # 记录开始时间
        # 这里提交任务，校验是否提交成功，并且获取任务ID
        print(url)
        logger.info(url)
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
                logger.info(progress)# 打印进度

                if progress['data'].get('images') and any(image for image in progress['data']['images'] if image is not None):
                    logger.info(f"任务完成，获取到图像数据。")
                    return progress
                logger.info(f"任务尚未完成，等待 {self.interval} 秒...")
                time.sleep(self.interval)
        else:
            return f'任务失败,原因：code {progress["msg"]}'
    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
    
    @filter.command("lib")
    async def lib(self, event: AstrMessageEvent):
        #user_name = event.get_sender_name()# 发送消息的用户昵称
        message_str = event.message_str # 用户发的纯文本消息字符串
        logger.info(f"获取用户文本：{message_str}")
        logger.info(f"文生图开始，生图类型为{self.imgType}")
        parts = message_str.split(" ",1)
        prompt = parts[1].strip() if len(parts) > 1 else ""# 获取用户发送的消息
        logger.info(f"获取用户提示词：{prompt}")
        Progess = self.text2img(prompt,self.width,self.height,self.steps)# 调用文生图接口
        logger.info(f"文生图结束，返回结果：{Progess}")
        pointsCost = Progess.get("data",{}).get("pointsCost",None)# 获取消耗点数
        accountBalance = Progess.get("data",{}).get("accountBalance",None)# 获取账户余额
        img_url = Progess.get("data",{}).get("images",[{}])[0].get("imageUrl",None)# 获取图片链接
        logger.info(f"获取图片链接：{img_url}")
        code = Progess.get("code",None)# 获取状态码
        msg = Progess.get("msg",None)#获取错误信息
        if code == 0:
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
