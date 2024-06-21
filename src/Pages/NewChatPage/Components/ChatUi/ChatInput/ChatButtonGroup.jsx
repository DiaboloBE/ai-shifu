import MainButton from "Components/MainButton.jsx";
import styles from './ChatButtonGroup.module.scss';
import { INTERACTION_OUTPUT_TYPE } from '@constants/courseContants.js';


/**
 * 聊天按钮组控件
 */
export const ChatButtonGroup = ({ type, props = [], onClick = (val) => {} }) => {
  const buttons = props.buttons;

  return (
    <div className={styles.buttonGroupWrapper}>
      <div className={styles.ChatButtonGroup}>
        {
          buttons.map((e) => {
            return <MainButton
              key={e.id}
              onClick={() => onClick?.(INTERACTION_OUTPUT_TYPE.SELECT, e.value)}
              style={{margin: '10px 0 0 10px'}}
            >{e.label}</MainButton>
          })
        }
      </div>
    </div>
  );
}

export default ChatButtonGroup;
