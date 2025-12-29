
/**
	车载log功能，需要搭配自研的上位机一起使用。
	使用端只用操作 Log_task::init()
	想要存入什么就使用link存入，例如：
	link(0,(u8*)&aaa,sizeof(aaa));   存入aaa，id为0。
	注意存入结构体需要保证结构体一字节对齐。
	bool full_error=0;           //缓存区满
	bool repeatId=0;             //有重复id

	autolink 已经自动存储所有的Virtual_Motor，imu，rc，power信息，不需要重复存储。


	Author:codeartist
	Date: 2024_12_06
*/
#include "log.h"
#include "usbd_cdc_core.h"
#include "usbd_core.h"
#include "usbd_usr.h"
#include "usb_conf.h"
#include "usbd_desc.h"
#include "crc.h"
#include "motor.h"
#include "power.h"
#include "info_task.h"
extern CDC_IF_Prop_TypeDef VCP_fops;
Log_task log_task;

#pragma pack()
Log_task::Log_task()
{
	// 初始化缓存区为400字节
	memset(Tx_Struct.Tx_Buf, 0, sizeof(Tx_Struct.Tx_Buf));
	current_offset = 0;
}

void Log_task::init() // 填入要存log的数据,限制id范围 0-50
{
	// link(0,(u8*)&aaa,sizeof(aaa));
	Log_Autolink();
}

void Log_task::run()
{
	Tx_Struct.frame_id++;
	Log_Auto_update();
	logData();
	Append_CRC16_Check_Sum((u8 *)&Tx_Struct, sizeof(Tx_Struct)); // 设置CRC16校验码
	VCP_fops.pIf_DataTx((uint8_t *)&Tx_Struct, sizeof(Tx_Struct));
}

void Log_task::logData()
{
	current_offset = 0; // 重置偏移量

	for (int i = 0; i < data_list.size(); i++)
	{
		// 检查缓存区是否有足够空间
		if (current_offset + 2 + data_list[i].size >= 400)
		{
			full_error = 1;
			return; // 如果没有足够空间，退出
		}

		// 按照顺序写入数据：0xA5, id, 数据内容
		Tx_Struct.Tx_Buf[current_offset++] = 0xA7;			  // 0xA5 标志
		Tx_Struct.Tx_Buf[current_offset++] = data_list[i].id; // 数据 ID

		// 拷贝数据内容到缓存区
		memcpy((u8 *)&Tx_Struct.Tx_Buf[current_offset], data_list[i].data, data_list[i].size);
		current_offset += data_list[i].size; // 更新当前偏移量
	}
	Tx_Struct.Tx_Buf[current_offset] = 0xa7;
}

void Log_task::link(uint8_t id, const uint8_t *data, uint8_t size)
{
	if (data_list.size() >= 40)
	{
		full_error = 1;
		return;
	}
	for (int i = 0; i < data_list.size(); i++)
	{
		if (data_list[i].id == id)
		{
			repeatId = 1;
			return;
		}
	}
	DataItem new_item = {id, data, size};
	data_list.push_back(new_item);
}


void Log_task::Log_Autolink()  // 放在所有任务初始化之后
{
	//遍历电机
	for (int i = 0; i < 2; i++)
	{
		for (int j = 0; j < 12; j++)
		{
			if (motorList[i][j].motorPoint != nullptr)
			{
				Motor_Log motor_Log;
				motor_Log.CanInfo = &motorList[i][j].motorPoint->canInfo;
				motor_Log.type = motorList[i][j].motorPoint->motorInfo.type;
				motor_Log.can_x = motorList[i][j].motorPoint->motorInfo.can_x;
				motor_Log.std_ID = motorList[i][j].motorPoint->motorInfo.Rec_ID;
				motor_Log_list.push_back(motor_Log);
			}
		}
	}
	
		Motor_Log motor_Log;
//		motor_Log.CanInfo = &gimbaltask.pitchMotor->canInfo;
//		motor_Log.type =	gimbaltask.pitchMotor->motorInfo.type ;
//		motor_Log.can_x = gimbaltask.pitchMotor->motorInfo.can_x;
//		motor_Log.std_ID = gimbaltask.pitchMotor->motorInfo.Rec_ID;
		motor_Log_list.push_back(motor_Log);
	

	for (int i = 0; i < motor_Log_list.size(); i++)
	{
		link(50 + i, (u8 *)&motor_Log_list[i], sizeof(motor_Log_list[i]));
	}

	link(80, (u8 *)&imu_Log, sizeof(imu_Log));

	link(81, (u8 *)&rc_Log, sizeof(rc_Log));

	link(82, (u8 *)&power_Log, sizeof(power_Log));
}

extern uint8_t dbusOfflineFlag;
void Log_task::Log_Auto_update()
{
	for (int i = 0; i < motor_Log_list.size(); i++)
	{
		motor_Log_list[i].encoder = motor_Log_list[i].CanInfo->encoder;
		motor_Log_list[i].speed = motor_Log_list[i].CanInfo->speed;
		motor_Log_list[i].trueCurrent = motor_Log_list[i].CanInfo->trueCurrent;
		motor_Log_list[i].temperature = motor_Log_list[i].CanInfo->temperature;
		motor_Log_list[i].totalAngle_f = motor_Log_list[i].CanInfo->totalAngle_f;
		motor_Log_list[i].totalRound = motor_Log_list[i].CanInfo->totalRound;
		motor_Log_list[i].lostFlag = motor_Log_list[i].CanInfo->lostFlag;
	}

	imu_Log.acc[0] = boardImu->acc.accValue.data[0];
	imu_Log.acc[1] = boardImu->acc.accValue.data[1];
	imu_Log.acc[2] = boardImu->acc.accValue.data[2];
	imu_Log.gyro[0] = boardImu->gyro.dps.data[0];
	imu_Log.gyro[1] = boardImu->gyro.dps.data[1];
	imu_Log.gyro[2] = boardImu->gyro.dps.data[2];
	memcpy(&imu_Log.Angle, &boardImu->AHRS_data.Angle, sizeof(imu_Log.Angle));
	imu_Log.watchtemp = watchtemp;

#if USE_RC
	memcpy(rc_Log.CH, RC.Key.CH, sizeof(RC.Key.CH));
	rc_Log.wheelCode = RC.Key.wheelCode;
	rc_Log.W = RC.Key.W;
	rc_Log.S = RC.Key.S;
	rc_Log.A = RC.Key.A;
	rc_Log.D = RC.Key.D;
	rc_Log.SHIFT = RC.Key.SHIFT;
	rc_Log.CTRL = RC.Key.CTRL;
	rc_Log.Q = RC.Key.Q;
	rc_Log.E = RC.Key.E;
	rc_Log.R = RC.Key.R;
	rc_Log.F = RC.Key.F;
	rc_Log.G = RC.Key.G;
	rc_Log.Z = RC.Key.Z;
	rc_Log.X = RC.Key.X;
	rc_Log.C = RC.Key.C;
	rc_Log.V = RC.Key.V;
	rc_Log.B = RC.Key.B;
	rc_Log.offlineFlag = dbusOfflineFlag;
#endif
}
