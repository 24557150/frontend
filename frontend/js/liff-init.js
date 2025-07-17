const liffId = "2007733246-nAexA2b9"; // 請換成你的實際 LIFF ID

async function initializeLiff() {
  try {
    await liff.init({ liffId });
    if (!liff.isLoggedIn()) {
      liff.login();
    } else {
      const profile = await liff.getProfile();
      window.globalUserId = profile.userId;
      console.log("登入成功，用戶 ID:", profile.userId);
    }
  } catch (err) {
    console.error("LIFF 初始化失敗:", err);
  }
}

document.addEventListener("DOMContentLoaded", initializeLiff);
