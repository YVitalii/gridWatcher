const net = require('net');

const CONFIG = {
    host: '192.168.1.132',
    port: 8899,
    loggerSn: 2956793531,
    unitId: 0x01
};

// --- СЛУЖБОВІ ФУНКЦІЇ (CRC16 та V5 Frame) ---
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

// --- ПІДГОТОВКА ЗАПИТУ ---
// Читаємо блок регістрів від 572 (0x023C) до 632 (щоб охопити всі ваші потреби)
const START_REG = 572;
const COUNT_REG = 60; 

const modbusPdu = Buffer.alloc(6);
modbusPdu[0] = CONFIG.unitId;
modbusPdu[1] = 0x03;
modbusPdu.writeUInt16BE(START_REG, 2);
modbusPdu.writeUInt16BE(COUNT_REG, 4);

const socket = new net.Socket();

socket.connect(CONFIG.port, CONFIG.host, () => {
    socket.write(buildSolarmanV5Frame(modbusPdu));
});

socket.on('data', (data) => {
    // Шукаємо початок Modbus відповіді (ID:01, FC:03, Len:...)
    const offset = data.indexOf(Buffer.from([0x01, 0x03]));
    
    if (offset !== -1) {
        // Дані починаються після SlaveID(1), FC(1) та ByteCount(1) = 3 байти
        const registers = data.slice(offset + 3);

        // Функція для зручного зчитування за номером регістра
        const getReg = (regAddr) => registers.readInt16BE((regAddr - START_REG) * 2);

        const inverterData = {
            timestamp: new Date().toISOString(),
            battery: {
                soc: getReg(588),               // %
                power_w: getReg(590)            // + розряд, - заряд
            },
            grid: {
                voltage_l1: getReg(598) / 10,   // V
                voltage_l2: getReg(599) / 10,   // V
                voltage_l3: getReg(600) / 10    // V
            },
            consumption: {
                load_w: getReg(625)             // Watts
            },
            solar: {
                pv_total_w: getReg(572)         // Watts
            }
        };

        // ВИВІД У JSON
        console.log(JSON.stringify(inverterData, null, 2));
    } else {
        console.error("❌ Не вдалося знайти Modbus дані у відповіді");
    }
    socket.destroy();
});

socket.on('error', (err) => console.error('🚨 Помилка:', err.message));