# AstrBot LiblibAPI 插件

一个强大的AI文生图插件，基于LiblibAI的API服务，支持多种绘图模式和自定义模型配置。

## 实际效果展示

### 基础绘图效果
![基础绘图效果](https://github.com/machinad/astrbot_plugin_liblibapi/blob/master/src/10003.png)

_使用基础绘图命令生成的图片效果展示_

### 提示词翻译效果
![提示词翻译效果](https://github.com/machinad/astrbot_plugin_liblibapi/blob/master/src/10004.png)

_展示中文提示词自动翻译为优化的英文提示词的效果_

### 自定义模型效果
![自定义模型效果](https://github.com/machinad/astrbot_plugin_liblibapi/blob/master/src/10005.png)

_使用自定义模型和LoRA生成的精美图片效果_

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

### 配置参数详解

### 插件配置界面
![插件配置界面](https://github.com/machinad/astrbot_plugin_liblibapi/blob/master/src/10006.png)

_插件配置界面展示了所有可配置的参数和选项_

#### 基础配置

##### 必填参数
- `AccessKey`：从LiblibAI获取的访问密钥
  - 用途：用于API身份验证
  - 获取方式：访问 https://www.liblib.art/apis 注册并获取
  - 默认值：AccessKey

- `SecretKey`：从LiblibAI获取的密钥
  - 用途：用于API身份验证
  - 获取方式：与AccessKey一同获取
  - 默认值：SecretKey

##### 图像生成参数
- `text_imgType`：生成图片的模式
  - 可选值：
    - sd1.5/XL模式(可自定义模型)
    - flux模式
    - confyui模式
  - 默认值：sd1.5/XL模式(可自定义模型)

- `width`：生成图片宽度
  - 用途：控制输出图片的宽度分辨率
  - 默认值：1024
  - 建议：根据需求调整，但要注意较大的分辨率会增加生成时间

- `height`：生成图片高度
  - 用途：控制输出图片的高度分辨率
  - 默认值：1024
  - 建议：根据需求调整，但要注意较大的分辨率会增加生成时间

- `num_inference_steps`：推理步数
  - 用途：控制图像生成的精细程度
  - 默认值：28
  - 说明：数值越大生成质量越高，但速度越慢

- `seed`：随机种子
  - 用途：控制图像生成的随机性
  - 默认值：-1（随机种子）
  - 说明：固定seed可以生成相同的图像

##### 提示词翻译配置
- `prompt_Translation`：提示词翻译设置
  - `is_Translation`：是否启用翻译
    - 类型：布尔值
    - 默认值：false
  - `Translation_Type`：翻译类型
    - 可选值：
      - sd格式提示词：转换为SD模型优化的提示词格式
      - 英语直译(自然语言)：直接翻译为自然英语
      - 中译中(ai润色)：优化中文描述

### 绘图模式配置

根据选择的`text_imgType`，需要配置对应模式的参数：

#### 1. SD1.5/XL模式配置
- `sd1.5/xl_config`：SD1.5/XL模式的专用配置
  - `is_SdLora`：是否使用lora模型
    - 类型：布尔值
    - 默认值：false
    - 说明：启用后会应用LoRA模型增强效果
  
  - `modelId`：大模型ID
    - 类型：字符串
    - 默认值：0ea388c7eb854be3ba3c6f65aac6bfd3
    - 获取方式：从模型详情页URL中的versionUuid参数获取
    - 说明：必须选择与模式版本匹配的模型（SD1.5或SDXL）
  
  - `sd_lora_modelid`：LoRA模型ID
    - 类型：字符串
    - 默认值：31360f2f031b4ff6b589412a52713fcf
    - 说明：仅在启用LoRA时生效，必须与大模型版本匹配
  
  - `sd_lora_scale`：LoRA权重
    - 类型：浮点数
    - 默认值：0.9
    - 说明：控制LoRA效果的强度，范围通常在0-1之间

#### 2. Flux模式配置
- `flux_config`：Flux模式的专用配置
  - `is_fluxLora`：是否使用lora模型
    - 类型：布尔值
    - 默认值：false
    - 说明：启用后会应用Flux专用的LoRA模型
  
  - `flux_lora_modelid`：Flux LoRA模型ID
    - 类型：字符串
    - 默认值：169505112cee468b95d5e4a5db0e5669
    - 说明：仅支持Flux版本的LoRA模型
  
  - `flux_lora_scale`：LoRA权重
    - 类型：浮点数
    - 默认值：0.9
    - 说明：控制Flux LoRA效果的强度

#### 3. ComfyUI模式配置（详情请参考高级用户 - Confyui工作流）
- `confyui_overwriting`：ComfyUI的API配置
  - 类型：文本（JSON格式）
  - 用途：自定义API调用配置
  - 支持的占位符：
    - {{prompt}}：提示词
    - {{height}}：高度
    - {{width}}：宽度
    - {{seed}}：随机种子
    - {{steps}}：推理步数
  - 示例：
    ```json
    {
      "prompt": "{{prompt}}",
      "height": {{height}},
      "width": {{width}},
      "seed": {{seed}},
      "steps": {{steps}}
    }
    ```

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

### 提示词测试命令(已经废弃，请无视这个命令)

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
   - 将复制的API配置JSON粘贴到confyui的api覆写文本框中
   - 为了方便自定义API调用插件配置，可以把以下几个占位符填入API对应的值中：{{prompt}}:提示词、{{height}}:高度、{{width}}:宽度、{{seed}}:随机种子、{{steps}}:推理步数。用法示例{"prompt":"{{prompt}}","height":{{height}}, "width":{{width}}, "seed":{{seed}}, "steps":{{steps}} }
2. API配置示例：
```json
{
    "templateUuid": "4df2efa0f18d46dc9758803e478eb51c",
    "generateParams": {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 377101986110064,
                "steps": 28,
                "cfg": 7
            }
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "2f32e43f45134387833cb87fa4122df5"
            }
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": {{width}},
                "height": {{height}}
            }
        },
        "18": {
            "class_type": "LoraLoader",
            "inputs": {
                "lora_name": "4005bc6195d54ee79bbce75bc7c7d7aa",
                "strength_model": 0.8999999999999999
            }
        },
        "19": {
            "class_type": "JjkText",
            "inputs": {
                "text": "{{prompt}}"
            }
        },
        "20": {
            "class_type": "LatentUpscaleBy",
            "inputs": {
                "scale_by": 2
            }
        },
        "workflowUuid": "955b8928c9604ef3931bbd35d08a4239"
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
