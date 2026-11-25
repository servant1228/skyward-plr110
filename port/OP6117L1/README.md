# OnePlus ACE 6T

按 **ColorOS 完整固件版本**选包，不要跨行混刷：

- `PLR110_17.0.1.200(CN01)`：[下载基础日用正式版](https://github.com/servant1228/skyward-plr110/releases/tag/ace6t-17.0.1.200) · [支持范围、校验、构建与回退](PUBLIC-200.md)。发布附件就是已验收的原版 RC1。
- `PLR110_17.0.0.101(CN01)`：[R7 预发行](https://github.com/servant1228/skyward-plr110/releases/tag/ace6t-r7)，说明如下。

## R7 预发行（仅 .101）

适用机型：PLR110 / OP6117L1，固件基线：PLR110_17.0.0.101(CN01)。基于 [kirklin/skyward](https://github.com/kirklin/skyward) 0.5.1。

- R7 固定设备显示名为 OnePlus ACE 6T，OS 版本不显示末尾的 release-keys。不更改 OTA 版本比较。
- 此前诊断版已在真机验证亮屏、触控、机主共享存储。公开 R7 仅完成离线校验，尚未上机。额外用户可能遇到 Weaver 槽位查询失败，振动实感及 WLAN 扫描尚未确认。
- 保留原厂 adbd 和 ADB 认证，不预授权开发电脑；ADB 可能显示 unauthorized。本镜像不是 OEM 签名（AVB NONE），未提供 vbmeta 修改版。
- 请核对机型、固件、SHA-256 并保留原厂 recovery 备份。若 OTA 等待合并，先让 Android 完成更新。

## 构建

Windows 构建使用 build-arm64.ps1、Rust 1.100.0、Android NDK r29。历史脚本依赖本地原厂 recovery、触控组件和固定摘要的上一版镜像，不能仅靠干净检出复现。不要公开 hostadb 诊断镜像。

有原始 R7 和已核验的 target/stock/OP6117L1/recovery_a.img 时，在项目根目录运行：

~~~powershell
python port/OP6117L1/build-public.py <原始R7路径>
~~~

打包依赖 Python 3.11+、lz4、target/avbtool.py。成品和校验文件在 out/public/。
