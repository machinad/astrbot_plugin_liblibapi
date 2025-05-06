# AstrBot LiblibAPI 插件

一个强大的AI文生图插件，基于LiblibAI的API服务，支持多种绘图模式和自定义模型配置。

## 功能特点

- 支持三种绘图模式：sd1.5/XL模式、flux模式和confyui模式
- 可自定义大模型和lora模型
- 支持中英文提示词（中文会自动翻译为英文提示词）
- 灵活的参数配置
- 支持自定义工作流

## 安装前准备

1. 注册LiblibAI账号
   - 访问 https://www.liblib.art/apis 注册账号
   - 获取AccessKey和SecretKey
   - 新用户赠送500积分

## 配置说明

### 基础配置

必填项：
- `AccessKey`：从LiblibAI获取的访问密钥
- `SecretKey`：从LiblibAI获取的密钥

可选配置：
- `width`：生成图片宽度（默认1024）
- `height`：生成图片高度（默认1024）
- `num_inference_steps`：推理步数，数值越大生成质量越高但速度越慢（默认28）

### 绘图模式配置

在`text_imgType`中选择以下模式之一：

1. **sd1.5/XL模式**
   - `modelId`：大模型ID
   - `is_SdLora`：是否使用lora模型（true/false）
   - `sd_lora_modelid`：lora模型ID
   - `sd_lora_scale`：lora权重（默认0.9）

2. **flux模式**
   - `is_fluxLora`：是否使用lora模型（true/false）
   - `flux_lora_modelid`：lora模型ID
   - `flux_lora_scale`：lora权重（默认0.9）

3. **confyui模式**（适合高级用户）
   - 需要自定义工作流配置

## 模型获取说明

### 模型选择

1. 访问 https://www.liblib.art/ 模型广场
2. 在右侧筛选条件中，必须勾选"生成图片可商用"选项
   - API调用仅支持可商用模型
   - 未标记可商用的模型将无法通过API使用

![模型筛选说明](https://github.com/machinad/astrbot_plugin_liblibapi/blob/master/src/10001.png)

_在筛选条件中勾选"生成图片可商用"选项_

### 模型版本匹配

选择模型时，请严格遵守以下版本对应规则：
- **SD1.5模式**：
  - 大模型必须选择SD1.5版本
  - LoRA模型也必须是SD1.5版本
- **SDXL模式**：
  - 大模型必须选择SDXL版本
  - LoRA模型也必须是SDXL版本
- **Flux模式**：
  - 仅支持Flux版本的模型和LoRA

不同版本的模型和LoRA无法混用，错误的搭配将导致生成失败。

### 获取模型ID

1. 在模型列表中点击想要使用的模型
2. 进入模型详情页面后，查看浏览器地址栏
3. 在URL中找到 `versionUuid=` 参数
4. `versionUuid=` 后面的字符串即为模型ID

示例：
```
https://www.liblib.art/modelDetail?versionUuid=6ab15bc284e0494ab4124d1c1744b56f
```
这里的 `6ab15bc284e0494ab4124d1c1744b56f` 就是模型ID

![模型ID获取说明](https://github.com/machinad/astrbot_plugin_liblibapi/blob/master/src/10002.png)

_在模型详情页面的地址栏中找到并复制模型ID_

## 使用方法

### 基础绘图命令

```
/limg <提示词>
```

示例：
- `/limg 1girl` - 生成一个女孩的图片
- `/limg 一个男孩，穿红色衣服` - 支持中文提示词

### 提示词测试命令

```
/ltest <提示词>
```
用于测试提示词翻译效果

## 高级用户 - Confyui工作流

### 工作流创建

1. 访问 LiblibAI工作流页面：https://www.liblib.art/workflows
2. 点击"创建工作流"按钮
3. 在工作流编辑器中：
   - 添加所需的节点和连接
   - 确保使用的所有模型都是可商用的
   - 设置适当的参数和默认值
   - 测试工作流是否能正常运行

### 发布为API

1. 工作流调试成功后，点击"发布"按钮
2. 选择"发布为AI应用"
3. 填写应用信息：
   - 设置应用名称和描述
   - 配置输入参数和说明
   - 设置默认参数值

### 获取API配置

1. 发布完成后，在应用详情页面：
   - 找到"API调用"部分
   - 复制API配置的JSON代码

### 配置使用

1. 在插件配置中：
   - 将绘图模式设置为"confyui模式"
   - 将复制的API配置JSON粘贴到对应的配置项中

2. API配置示例：
```json
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
```

### 使用建议

1. 参数设置：
   - 合理配置默认参数值
   - 预设常用的提示词和反向提示词
   - 根据需求调整图像尺寸和质量参数

2. 性能优化：
   - 适当降低采样步数以提升速度
   - 避免过于复杂的工作流
   - 定期测试工作流的稳定性

## 注意事项

1. 确保模型版本匹配：
   - sd1.5模型配sd1.5 lora
   - sdXL模型配sdXL lora
   - flux模型配flux lora
2. 仅支持可商用模型调用
3. 注意积分消耗

## 支持

如有问题，请访问：
- [AstrBot官方文档](https://astrbot.app)
- [插件仓库](https://github.com/machinad/astrbot_plugin_liblibapi.git)
