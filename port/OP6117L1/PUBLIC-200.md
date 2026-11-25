# OnePlus ACE 6T · .200 基础日用正式版

**[正式版下载](https://github.com/servant1228/skyward-plr110/releases/tag/ace6t-17.0.1.200)**：原版 RC1 通过机主验收后原样发布，保留原文件名，不是 vbmetafixed 变体。 只面向 `PLR110 / OP6117L1`、`PLR110_17.0.1.200(CN01)`、独立 A/B recovery。未验证其他固件、同平台其他手机或其他引导链。

发布镜像：`skyward-OP6117L1-17.0.1.200-rc1.img`，100 MiB；整镜像 SHA-256：`1fff158f68343a553a7405b4651cb6bbaa127680ce7905d21675fc26a9d3f06c`。相同编译产物两次打包逐字节一致。与 R13 逐项比对：移除诊断接收器，恢复原厂 logd 声明与 ADB 信任，以发布构建的 recovery 和 system-init 替换旧程序；机型配置未变。

[Ubuntu 24.04 CI（`4de5091`）](https://github.com/servant1228/skyward-plr110/actions/runs/45595017986)：`skyward-config` 配置测试 29/29，WLAN 有界重试测试 5/5。此结果不等于整个工作区或所有手机功能均已测试。先前 Windows 主机的配置测试为 13/29（包含把 Android 绝对路径按 Windows 语义处理的失败）。

## 哪些结果来自真机？

- 同固件本机测试版 R13：亮屏与触控可操作；正常存储打开流程返回“仍关闭的用户：[]”；一次冷启动首开 WLAN 即显示扫描列表；手动打开文件传输后 Windows 枚举 MTP 设备，同时保留认证 ADB。没有测试 MTP 文件拷贝、WLAN 连接或联网。
- 先前的 R11 在同一启动中留置 10 分 50 秒，未再发生原来的五分钟自动重启。不能据此承诺长时间刷写操作。未验证带密码的其他用户、备份还原、刷包/OTA 或双系统，不将这些功能列为正式支持。
- 机主明确确认使用的是未改动的 `rc1.img`，并反馈实际进入后测试无异常。认证 ADB 独立核对了运行中的 recovery、设备配置、system-init、init.rc 和 adbd，以及原厂 ADB 授权链接。整镜像校验来自本地待发附件，而非对手机分区的回读；机主整体验收不等于每个功能都做过独立测试。
- RC1 使用原厂 adbd、原厂授权链接及 `ro.adb.secure=1`；无本地预授权主机或 eSE 诊断接收器。公开包上 ADB 对不受信任的电脑显示 `unauthorized` 属于预期，不要关闭认证。MTP 与 ADB 认证无关，每次进 recovery 默认关闭；只在信任所连电脑时手动开启。

## 安装前核对与回退

1. 核对下载文件的整镜像 SHA-256、设备代号、**当前**完整固件、活动槽、OTA 快照/合并状态；当前槽的同固件原厂 recovery 须已有可读、校验过的独立备份，且有自己验证可用的回退通道。任一条件不明则停止。此包不是 OEM 签名；AVB 摘要校验或界面显示 locked/green 均不证明设备会接受它。
2. 如要在自己的设备上复核，请检查亮屏/触控及正常机主存储状态、振动开/关、冷启动 WLAN 首次显示列表。手动开 MTP 后确认 Windows 识别设备，再关闭确认设备退出；不要求查看文件、连接网络、改密码或反复解密。
3. 覆盖原五分钟时点，最后用菜单正常重启系统，确认回到原 ColorOS。记录通过或未测；不把诊断版验收替代公开版验收。
4. 安装或回退均只使用已确认适用的方式和匹配的 recovery 分区。若需要回退，仅用自己留存的**同固件、对应槽**原厂 recovery；不要靠切槽、改 vbmeta、关闭验证或格式化 data 来补救。不提供原厂回退镜像。

## 离线构建

不需要连接手机、读取电脑 ADB 密钥、下载私用镜像或运行任何旧诊断脚本。Windows：Rust 1.100.0 (GNU)、NDK r29、Python 3.11+、`lz4` 和 AOSP `avbtool.py`（放在 `target/avbtool.py`）；本地工具链目录约定见 `build-arm64.ps1`。还需要从合法来源自行取得：

- `target/stock/OP6117L1/17.0.1.200/recovery_b.img`；SHA-256：`6bd5433e80bbbd4c86b0930242d6489710f003535d9257051d3977fb89325be4`。
- 同目录下的 `touch/`：匹配固件的 HBP5 服务及配套 NDK 库；所需文件名和摘要固定在 `build-17.0.1.200.py`，不单独分发。

从仓库根目录运行：

~~~powershell
./port/OP6117L1/build-arm64.ps1 -Public
python port/OP6117L1/build-public-200.py
~~~

脚本从上述原厂底包重建，验证 ARM64 程序、厂商输入、原厂 ADB 策略、ramdisk 复解包与 AVB 哈希。成品及 SHA-256 在 `out/public/`；拒绝覆盖已有 RC1。AVB 算法为 NONE，不是 OEM 签名。只分发经过验收的公开镜像和校验文件，不分发本机 ADB 版、诊断日志、私钥、单独的厂商组件或回退镜像。
