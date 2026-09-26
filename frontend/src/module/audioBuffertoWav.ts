export function audioBufferToWav(buffer: AudioBuffer): ArrayBuffer {
    const numChannels = buffer.numberOfChannels;
    const sampleRate = buffer.sampleRate;
    const format = 1; // PCM
    const bitDepth = 16;
  
    const resultLength = buffer.length * numChannels * 2 + 44;
    const result = new ArrayBuffer(resultLength);
    const view = new DataView(result);
  
    let offset = 0;
  
    const writeString = (str: string) => {
      for (let i = 0; i < str.length; i++) {
        view.setUint8(offset++, str.charCodeAt(i));
      }
    };
  
    const writeUint32 = (value: number) => {
      view.setUint32(offset, value, true);
      offset += 4;
    };
  
    const writeUint16 = (value: number) => {
      view.setUint16(offset, value, true);
      offset += 2;
    };
  
    writeString("RIFF");
    writeUint32(resultLength - 8);
    writeString("WAVE");
    writeString("fmt ");
    writeUint32(16);
    writeUint16(format);
    writeUint16(numChannels);
    writeUint32(sampleRate);
    writeUint32(sampleRate * numChannels * bitDepth / 8);
    writeUint16(numChannels * bitDepth / 8);
    writeUint16(bitDepth);
    writeString("data");
    writeUint32(resultLength - offset - 4);
  
    const interleaved = new Float32Array(buffer.length * numChannels);
    for (let ch = 0; ch < numChannels; ch++) {
      const channel = buffer.getChannelData(ch);
      for (let i = 0; i < channel.length; i++) {
        interleaved[i * numChannels + ch] = channel[i];
      }
    }
  
    for (let i = 0; i < interleaved.length; i++) {
      const s = Math.max(-1, Math.min(1, interleaved[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
      offset += 2;
    }
  
    return result;
  }
  