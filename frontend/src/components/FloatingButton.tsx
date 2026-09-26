import React from 'react';
import styles from './FloatingButton.module.css';

type FloatingButtonProps = {
  onClick: () => void;
  label?: string;
};

const FloatingButton: React.FC<FloatingButtonProps> = ({ onClick, label = "Ask Realtor" }) => {
  return (
    <button
      className={styles.floatingButton}
      onClick={onClick}
      aria-label={label}
      title={label}
    >
      📞 Talk with Assistant
    </button>
  );
};

export default FloatingButton;
