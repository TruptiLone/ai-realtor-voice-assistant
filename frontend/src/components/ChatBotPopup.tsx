import React from 'react';
import VoiceChatbot from './VoiceChat';
import styles from './ChatBotPopup.module.css';

type Props = {
  onClose: () => void;
  propertyId: number;
  simulateUserMessage: (transcript: string, audio_base64: string) => void;
  setMessages: React.Dispatch<React.SetStateAction<any[]>>;
};

const ChatbotPopup: React.FC<Props> = ({ onClose, simulateUserMessage, setMessages }) => {
  const handleEndChat = () => {
    // This just closes the popup; actual cleanup (mic/WebSocket) is handled in VoiceChatbot
    onClose();
  };

  return (
    <div className={styles.overlay}>
      <div className={styles.popup}>
        <button onClick={handleEndChat} className={styles.closeButton}>✖</button>
        <VoiceChatbot
         // simulateUserMessage={simulateUserMessage}
          //setMessages={setMessages}
         onClose={handleEndChat}
        />
      </div>
    </div>
  );
};

export default ChatbotPopup;
