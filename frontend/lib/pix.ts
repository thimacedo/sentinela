export function generatePixPayload(key: string, amount: number, merchantName: string, merchantCity: string): string {
  function formatField(id: string, value: string): string {
    const len = value.length.toString().padStart(2, '0');
    return id + len + value;
  }
  
  const payloadFormat = '000201';
  const gui = formatField('00', 'br.gov.bcb.pix');
  const pixKey = formatField('01', key);
  const merchantAccount = formatField('26', gui + pixKey);
  const mcc = formatField('52', '0000');
  const currency = formatField('53', '986');
  const amountField = amount > 0 ? formatField('54', amount.toFixed(2)) : '';
  const country = formatField('58', 'BR');
  
  // Nomes no PIX geralmente n\u00E3o devem ter acentos e devem ter tamanho limitado
  const cleanName = merchantName.substring(0, 25).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase();
  const cleanCity = merchantCity.substring(0, 15).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase();

  const mName = formatField('59', cleanName);
  const mCity = formatField('60', cleanCity);
  const additionalData = formatField('62', formatField('05', '***'));
  
  const payloadWithoutCrc = payloadFormat + merchantAccount + mcc + currency + amountField + country + mName + mCity + additionalData + '6304';
  
  // Calculate CRC16 CCITT-FALSE
  let crc = 0xFFFF;
  for (let i = 0; i < payloadWithoutCrc.length; i++) {
    crc ^= payloadWithoutCrc.charCodeAt(i) << 8;
    for (let j = 0; j < 8; j++) {
      if ((crc & 0x8000) !== 0) {
        crc = (crc << 1) ^ 0x1021;
      } else {
        crc = crc << 1;
      }
    }
  }
  
  // Converte para Hex, uppercase, com no m\u00EDnimo 4 d\u00EDgitos
  const crcHex = (crc & 0xFFFF).toString(16).toUpperCase().padStart(4, '0');
  return payloadWithoutCrc + crcHex;
}
