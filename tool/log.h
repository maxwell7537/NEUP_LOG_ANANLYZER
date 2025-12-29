#ifndef _LOG_H_
#define _LOG_H_

#include "board.h"
#include "time.h"
#include "task_virtual.h"
#include "motor.h"
#include "imu_task.h"
#include "bmi088.h"
#include "dbus.h"
// 数据项结构体，包含 id，地址和大小
struct DataItem
{
	uint8_t id = 0;			 // 数据的 ID
	const uint8_t *data = nullptr; // 数据的地址
	uint8_t size = 0;		 // 数据的大小
};

class Log_task
{
public:
	Log_task();

	void run();
	void Log_Auto_update();

	void init();
	void Log_Autolink();

	void link(uint8_t id, const uint8_t *data, uint8_t size);

	void logData();
	bool full_error = 0; // 缓存区满
	bool repeatId = 0;	 // 有重复id
private:
	myvector<DataItem, 80> data_list; // 数据列表 ,最多80个单位

#pragma pack(1)
	struct
	{
		uint8_t header = 0xA5; // 包头，默认0XA5
		u8 type = 6;

		uint8_t Tx_Buf[600] = {0}; // 600个字节的发送缓存区

		uint64_t time_stamp = 0;
		int16_t frame_id = 0; // 包序号
		uint8_t endheader = 0xB9;
		uint16_t CRC16CheckSum = 0; // 校验码
	} Tx_Struct;

	struct Motor_Log
	{
		u8 type = 0;			 ///< 电机类型
		u8 can_x = 0;			 ///< 挂载CAN总线[CAN_1 / CAN_2]
		uint32_t std_ID = 0;	 ///< 电机CAN总线反馈StdID
		uint16_t encoder = 0;	 ///< 原始机械编码器值
		int16_t speed = 0;		 ///< 原始机械转速
		int32_t trueCurrent = 0; // 实际电流
		int16_t temperature = 0; // 电机温度
		float totalAngle_f = 0.0f;	 ///< 总角度（浮点），与mpu6050单位相等
		int32_t totalRound = 0;	 ///< 总圈数
		u8 lostFlag = 0;		 // 掉线标志位
		CanInfo *CanInfo = nullptr;
	};

	myvector<Motor_Log, 20> motor_Log_list;

	struct Imu_Log
	{
		float acc[3] = {0.0f, 0.0f, 0.0f};  ///< 加速度解算数据
		float gyro[3] = {0.0f, 0.0f, 0.0f}; ///< 角速度解算数据
		float Angle[3] = {0.0f, 0.0f, 0.0f};
		float watchtemp = 0.0f; // 陀螺仪温度
	} imu_Log;

	struct RC_Log
	{
		int16_t CH[13] = {0};
		int32_t wheelCode = 0; // 鼠标滚轮编码值

		uint16_t W : 1;		///< 0x0001
		uint16_t S : 1;		///< 0x0002
		uint16_t A : 1;		///< 0x0004
		uint16_t D : 1;		///< 0x0008
		uint16_t SHIFT : 1; ///< 0x0010
		uint16_t CTRL : 1;	///< 0x0020
		uint16_t Q : 1;		///< 0x0040
		uint16_t E : 1;		///< 0x0080
		uint16_t R : 1;		///< 0x0100
		uint16_t F : 1;		///< 0x0200
		uint16_t G : 1;		///< 0x0400
		uint16_t Z : 1;		///< 0x0800
		uint16_t X : 1;		///< 0x1000
		uint16_t C : 1;		///< 0x2000
		uint16_t V : 1;		///< 0x4000
		uint16_t B : 1;		///< 0x8000

		u8 offlineFlag = 1;
	} rc_Log;

	struct Power_Log
	{
		uint16_t capacitance_percentage_t = 0; // 电容能量百分比[仅通讯用，模拟定点数]
		uint16_t maxCurrent_t = 0;			   // 最大电流[仅通讯用，模拟定点数]
		uint16_t currentNow_t = 0;			   // 当前电流[仅通讯用，模拟定点数]
		uint16_t capHealth = 0;				   // 当前电容电压过低，处于直通状态
		uint16_t errorCode = 0;				   // 功率错码
		u8 offlineFlag = 1;
	} power_Log;

#pragma pack()
	size_t current_offset = 0; // 当前偏移量
};

extern Log_task log_task;

#endif