from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import hmac
import base64
import time
import requests
from datetime import datetime
import hashlib
import uuid
@register("liblibApi", "machinad", "一个调取liblib在线工作流进行ai绘图的插件", "1.0.1")
class MyPlugin(Star):
    def __init__(self, context: Context, config: dict, interval=5):
        self.ak = config.get("AccessKey")
        self.sk = config.get("SecretKey")
        self.width= config.get("width")
        self.height = config.get("height")
        self.steps = int(config.get("num_inference_steps"))
        self.time_stamp = int(datetime.now().timestamp() * 1000)#获取当前时间戳
        self.signature_nonce = uuid.uuid1()#获取uuid
        self.signature_img = self._hash_sk(self.sk, self.time_stamp, self.signature_nonce)#获取签名
        self.signature_ultra_img = self._hash_ultra_sk(self.sk, self.time_stamp, self.signature_nonce)#获取签名
        self.signature_status = self._hash_sk_status(self.sk, self.time_stamp, self.signature_nonce)#获取签名
        self.interval = interval
        self.headers = {'Content-Type': 'application/json'}
        self.text2img_url = self.get_image_url(self.ak, self.signature_img, self.time_stamp,self.signature_nonce)#获取url
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

    def get_ultra_image_url(self, ak, signature, time_stamp, signature_nonce):

        url = f"https://openapi.liblibai.cloud/api/generate/webui/text2img/ultra?AccessKey={ak}&Signature={signature}&Timestamp={time_stamp}&SignatureNonce={signature_nonce}"
        return url

    def get_generate_url(self, ak, signature, time_stamp, signature_nonce):

        url = f"https://openapi.liblibai.cloud/api/generate/webui/status?AccessKey={ak}&Signature={signature}&Timestamp={time_stamp}&SignatureNonce={signature_nonce}"
        return url
    def text2img(self, message_str, width, height,steps):
        ""
        """
        文生图全示例 json
        """
        base_json = {
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
        user_name = event.get_sender_name()# 发送消息的用户昵称
        message_str = event.message_str # 用户发的纯文本消息字符串
        parts = message_str.split(" ",1)
        prompt = parts[1].strip() if len(parts) > 1 else ""
        img_url = self.text2img(prompt,self.width,self.height,self.steps)
        yield event.plain_result(img_url+user_name) # 发送一条纯文本消息
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
