const net = require('net');

const CONFIG = {
    host: '192.168.1.132',
    port: 8899,
    loggerSn: 2956793531,
    unitId: 0x01
};

// Конфігурація діапазону (60 регістрів)
const START_REG = 572; 
const COUNT_REG = 60; 

// --- СЛУЖБОВІ ФУНКЦІЇ ---
function crc16(buffer) {
    let crc = 0xFFFF;
    for (let i = 0; i < buffer.length; i++) {
        crc ^= buffer[i];
        for (let j = 0; j < 8; j++) {
            if (crc & 0x0001) crc = (crc >> 1) ^ 0xA001;
            else crc >>= 1;
        }
    }
    const crcBuf = Buffer.alloc(2);
    crcBuf.writeUInt16LE(crc); 
    return crcBuf;
}

function buildSolarmanV5Frame(modbusPdu) {
    const modbusRTU = Buffer.concat([modbusPdu, crc16(modbusPdu)]);
    const payload = Buffer.alloc(15 + modbusRTU.length);
    payload[0] = 0x02; 
    modbusRTU.copy(payload, 15);

    const header = Buffer.alloc(11);
    header[0] = 0xA5;
    header.writeUInt16LE(payload.length, 1);
    header.writeUInt16LE(0x4510, 3);
    header.writeUInt16LE(0x0011, 5);
    header.writeUInt32LE(CONFIG.loggerSn, 7);

    const frameParts = Buffer.concat([header, payload]);
    let checksum = 0;
    for (let i = 1; i < frameParts.length; i++) checksum += frameParts[i];
    
    return Buffer.concat([frameParts, Buffer.from([checksum & 0xFF, 0x15])]);
}

// --- ВИКОНАННЯ ---
const modbusPdu = Buffer.alloc(6);
modbusPdu[0] = CONFIG.unitId;
modbusPdu[1] = 0x03;
modbusPdu.writeUInt16BE(START_REG, 2);
modbusPdu.writeUInt16BE(COUNT_REG, 4);

const socket = new net.Socket();

socket.connect(CONFIG.port, CONFIG.host, () => {
    console.log(`📡 Запит 60 регістрів (${START_REG}-${START_REG + COUNT_REG - 1})...`);
    socket.write(buildSolarmanV5Frame(modbusPdu));
});

socket.on('data', (data) => {
    // Шукаємо маркер Modbus (ID:01, FC:03, ByteCount: 120 (60*2))
    const offset = data.indexOf(Buffer.from([0x01, 0x03, 0x78])); // 0x78 = 120
    
    if (offset !== -1) {
        const registers = data.slice(offset + 3);
        
        // Функція доступу до даних
        const getRaw = (addr) => registers.readInt16BE((addr - START_REG) * 2);

        const fullJson = {
            timestamp: new Date().toISOString(),
            status: {
                // Ми не читали 512, але якщо треба, START_REG має бути меншим
                raw_registers_range: `${START_REG} to ${START_REG + COUNT_REG - 1}`
            },
            solar: {
                pv_total_power_w: getRaw(572),
                pv1_voltage: getRaw(573) / 10,
                pv1_current: getRaw(574) / 10,
                pv2_voltage: getRaw(575) / 10,
                pv2_current: getRaw(576) / 10
            },
            battery: {
                soc: getRaw(588),
                voltage: getRaw(587) / 100,
                power_w: getRaw(590), // + розряд, - заряд
                current: getRaw(591) / 100,
                temperature: getRaw(586) / 10 - 100 // Спрощена формула
            },
            grid: {
                voltage_l1: getRaw(598) / 10,
                voltage_l2: getRaw(599) / 10,
                voltage_l3: getRaw(600) / 10,
                frequency: getRaw(601) / 100,
                total_grid_power: getRaw(616) // Активна потужність мережі
            },
            home_consumption: {
                total_load_w: getRaw(625),
                load_l1: getRaw(622),
                load_l2: getRaw(623),
                load_l3: getRaw(624)
            }
        };

        console.log(JSON.stringify(fullJson, null, 2));
    } else {
        console.log("⚠️ Відповідь отримана, але масив 60 регістрів не розпізнано. Перевірте HEX.");
        console.log("Raw HEX:", data.toString('hex'));
    }
    socket.destroy();
});

socket.on('error', (err) => console.error('🚨 Помилка:', err.message));