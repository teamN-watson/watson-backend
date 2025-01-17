import { create } from "zustand"; // named export 사용


const useStore = create((set) => ({
  isLoggedIn: false,
  userInfo: null,
  accessToken: null,
  refreshToken: null,
  setUserInfo: (userInfo) => set({ userInfo, isLoggedIn: true }),
  setAccessToken: (token) => set({ accessToken: token }),
  setRefreshToken: (token) => set({ refreshToken: token }),
  login: (userInfo, accessToken, refreshToken) => {
    sessionStorage.setItem('access_token', accessToken);
    sessionStorage.setItem('refresh_token', refreshToken);
    set({
      userInfo,
      isLoggedIn: true,
    });
  },
  logout: () => set({ isLoggedIn: false, userInfo: null, accessToken: null, refreshToken: null }),
}));

export default useStore;
