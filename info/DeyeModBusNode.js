const net = require('net');

const CONFIG = {
    host: '192.168.1.132',
    port: 8899, 
    loggerSn: 2956793531,
    unitId: 0x01
};

// CRC16 для Modbus RTU завжди Little Endian
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
    // Внутрішній Modbus RTU пакет (PDU + CRC)
    const modbusRTU = Buffer.concat([modbusPdu, crc16(modbusPdu)]);
    
    // Payload: 15 байт заголовка Solarman + Modbus пакет
    const payload = Buffer.alloc(15 + modbusRTU.length);
    payload[0] = 0x02; // Frame Type (Inverter)
    payload.writeUInt16LE(0x0000, 1); // Sensor Type
    payload.writeUInt32LE(0x00000000, 3); // Total Working Time
    payload.writeUInt32LE(0x00000000, 7); // Power On Time
    payload.writeUInt32LE(0x00000000, 11); // Offset Time
    modbusRTU.copy(payload, 15);

    // Header: 11 байт (Little Endian для довжини та S/N)
    const header = Buffer.alloc(11);
    header[0] = 0xA5; // Start byte
    header.writeUInt16LE(payload.length, 1); // ДОВЖИНА PAYLOAD
    header.writeUInt16LE(0x4510, 3);         // Control Code (Little Endian)
    header.writeUInt16LE(0x0011, 5);         // Sequence / Serial
    header.writeUInt32LE(CONFIG.loggerSn, 7); // Logger S/N (Little Endian)

    const frameWithoutTrailer = Buffer.concat([header, payload]);
    
    // Checksum Solarman (рахується від байта 1 до кінця payload)
    let checksum = 0;
    for (let i = 1; i < frameWithoutTrailer.length; i++) {
        checksum += frameWithoutTrailer[i];
    }
    
    const trailer = Buffer.from([checksum & 0xFF, 0x15]); // Checksum + End byte

    return Buffer.concat([frameWithoutTrailer, trailer]);
}

// Побудова Modbus запиту (BIG ENDIAN для адрес і значень)
const modbusPdu = Buffer.alloc(6);
modbusPdu[0] = CONFIG.unitId; // Slave ID
modbusPdu[1] = 0x03;          // Read Holding Registers
modbusPdu.writeUInt16BE(0x0200, 2); // Start Address: 512
modbusPdu.writeUInt16BE(0x0001, 4); // Count: 1

const socket = new net.Socket();
socket.connect(CONFIG.port, CONFIG.host, () => {
    console.log('✅ TCP Connected. Sending Solarman V5 frame...');
    const frame = buildSolarmanV5Frame(modbusPdu);
    socket.write(frame);
});

socket.on('data', (data) => {
    const hex = data.toString('hex');
    console.log('📩 Отримано відповідь:', hex);
    
    // Шукаємо початок Modbus пакета: наш Slave ID (01) та код функції (03)
    // У вашому пакеті це зазвичай після байта '69'
    const modbusStartIndex = data.indexOf(Buffer.from([0x01, 0x03, 0x02]));

    if (modbusStartIndex !== -1) {
        const value = data.readUInt16BE(modbusStartIndex + 3);
        console.log('✅ УСПІХ!');
        console.log(`📊 Значення регістру (Статус інвертора): ${value}`);
        
        if (value === 0) console.log("📝 Стан: Standby (Очікування)");
        if (value === 1) console.log("📝 Стан: Self-check (Самоперевірка)");
        if (value === 2) console.log("📝 Стан: Normal (Робота)");
    } else {
        console.log('⚠️ Дані отримано, але формат Modbus не розпізнано. Перевірте HEX.');
    }
    socket.destroy();
});