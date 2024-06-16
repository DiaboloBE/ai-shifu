import { create } from 'zustand';
import { getUserInfo, registerTmp } from '@Api/user.js';
import { userInfoStore, tokenTool } from '@Service/storeUtil.js';
import { genUuid } from '@Utils/common.js';
import { verifySmsCode } from '@Api/user.js';

export const useUserStore = create((set) => ({
  hasLogin: false,
  userInfo: null,

  login: async ({mobile, smsCode}) => {
    const res = await verifySmsCode({mobile, sms_code: smsCode });
    const { userInfo, token } = res.data;
    set(() => ({
      hasLogin: true,
      userInfo,
    }));

    tokenTool.set({ token, faked: false });
  },

  // 通过接口检测登录状态
  checkLogin: async () => {
    if (!tokenTool.get().token) {
      set(() => ({
        hasLogin: false,
        userInfo: null,
      }));

      const res = await registerTmp({ temp_id: genUuid() });
      const token = res.data.token;
      tokenTool.set({ token, faked: true });
      return
    }

    if (userInfoStore.get()) {
      set(() => ({
        userInfo: JSON.parse(userInfoStore.get()),
      }));
    }

    try {
      const res = await getUserInfo();
      const userInfo = res.data;

      if (userInfo.mobile) {
        set(() => ({
          hasLogin: true,
          userInfo,
        }));

        tokenTool.set({ token: tokenTool.get().token, faked: false });
      } else {
        set(() => ({
          hasLogin: false,
          userInfo: userInfo,
        }));
        tokenTool.set({ token: tokenTool.get().token, faked: true });
      }
    } catch (err) {
      if (err.status && err.status === 403) {
        set(() => ({
          hasLogin: false,
          userInfo: null,
        }));

        const res = await registerTmp({ temp_id: genUuid() });
        const token = res.data.token;
        tokenTool.set({ token, faked: true });
      }
    }
  },

  logout: async () => {
    set(() => {
      userInfoStore.remove();
      tokenTool.remove();
      return {
        hasLogin: false,
        userInfo: null,
      };
    })
  },
}));
