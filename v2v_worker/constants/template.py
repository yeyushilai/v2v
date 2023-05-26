# -*- coding: utf-8 -*-


# 通用模板
###############################################################################
SSH_CMD_OPTION = '''-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'''
SSH_CMD_TEMPLATE = '''ssh -i {id_rsa} {option} {user}@{host} {action}'''
SCP_CMD_TEMPLATE = '''scp -i {id_rsa} {option} {src_path} {user}@{host}:{dst_path}'''
###############################################################################


# 导出镜像
###############################################################################
EXPORT_IMAGE_CMD_TEMPLATE = '''{ovf_tool_path} {common_params} {advanced_params} '{cmd_prefix}{username}:{password}@{ip}:{port}/{datacenter}/{vm_dir}/{vm_folder}/{src_vm_name}' '{dst_dir}/{dst_vm_name}.{dst_image_format}' '''
###############################################################################


# 上传镜像
###############################################################################
UPLOAD_IMAGE_COMPILE_NFS_CMD_TEMPLATE = '''gcc -fPIC -shared -o {ld_nfs_so_file_path} {ld_nfs_c_file_path} -ldl -lnfs'''
###############################################################################


# 处理镜像
###############################################################################
DEAL_IMAGE_CONVERT_IMAGE_CMD_TEMPLATE = '''{qemu_img_path} {qemu_img_action} -p -f {src_image_format} -O {dst_image_format} {src_image_path} {dst_image_path} '''
# DEAL_IMAGE_SANC_COMMON_CMD_TEMPLATE = '''{qemu_img_path} {qemu_img_action} -O {image_format} {image_path} {volume_path} '''
###############################################################################


# 创建虚拟机
###############################################################################
CREATE_INSTANCE_INSERT_IMAGE_TEMPLATE = dict(
    description='',
    architecture='''x86_64''',
    # 镜像支持的处理器类型，有效值为 64位 ( 64bit ) 和 32位 ( 32bit )
    processor_type='''64bit''',
    hypervisor='''kvm''',

    # 镜像状态，有效值为pending, available, deprecated, suspended, deleted, ceased。
    # pending： 等待被创建
    # available： 可用状态，此时可以基于该镜像创建云服务器。
    # deprecated： 已被弃用，此时不再可以基于该镜像创建新的云服务器，但不影响已有云服务器的正常使用。
    # suspended： 由于欠费，已被暂停使用
    # deleted： 已被删除，但处于此状态的镜像在2小时之内仍可以被恢复为 available 状态
    # ceased： 已被彻底删除，处于此状态的镜像无法恢复
    status='''available''',
    sub_code=0,

    # 镜像过渡状态，有效值为creating, suspending，resuming，deleting，recovering。
    # creating： 创建中，由 pending 状态变成 available 状态
    # suspending： 欠费暂停中，由 available 状态变成 suspended 状态
    # resuming： 恢复中，由 suspended 状态变成 available 状态
    # deleting： 删除中，由 available/suspended 状态变成 deleted 状态
    # recovering： 恢复中，由 deleted 状态变成 available 状态
    transition_status='''''',

    # 镜像的可见范围，有效值为 public 和 private
    # public: 对所有人可见，例如系统提供的镜像
    # private: 只对镜像所有者可见，例如用户的自有镜像
    visibility='''private''',
    ui_type='''tui''',
    video_type='''vga''',
    video_ram=9126,

    # 运行该镜像的推荐云服务器配置
    recommended_type='''c1m1''',
    format='''qcow2''',
    controller='''self''',
    sound_type='''ac97''',
    f_resetpwd=1,
    lang='''en-us''',
    app_billing_id='''''',
    root_partition_number=0,

    # 可选None、pitrix,
    # 用于云平台获取虚机监控信息
    agent_type='''pitrix''',

    # 可选''''''或者lvm
    root_partition_fs='''''',

    # 镜像类型，0表示普通镜像，1表示ISO镜像
    image_type=0,

    # 4表示平台只运行虚机，不支持改密码，支持硬盘热拔插
    # 7表示不改密，硬盘需要关机挂载
    features=4
)

CREATE_INSTANCE_STOP_INSTANCE_CMD_TEMPLATE = '''virsh destroy {instance_id}'''
###############################################################################


# 覆盖镜像
###############################################################################
CONVERT_IMAGE_SANC_VOS_CMD_TEMPLATE = '''{qemu_img_qbd_path} {qemu_img_action} -p -n {image_path} -O raw qbd:vol/{volume_id}.img:conf=/etc/neonsan/qbd.conf:type=tcp '''
###############################################################################


# 磁盘相关
###############################################################################
# qbd
GET_POOL_BY_VOLUME_CMD_TEMPLATE = """qbd -l | grep {volume_id} | awk -F ' ' '{{print $4}}' | awk -F '/' '{{print $1}}'"""
QBD_MAP_CMD_TEMPLATE = """qbd -m {pool}/{volume_id}"""
QBD_UNMAP_CMD_TEMPLATE = """qbd -u {pool}/{volume_id}"""
QBD_DEV_PATH_TEMPLATE = """/dev/qbd/{pool}/{volume_id}.img"""
MOUNT_QBD_DEVICE_CMD_TEMPLATE = """mount /dev/qbd/{pool}/{volume_id}.img {mount_dir}"""
UMOUNT_CMD_TEMPLATE = '''umount {mount_dir}'''
###############################################################################