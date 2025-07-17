// static/js/liff-init.js
async function initLiffAndGetUserId(liffId) {
  if (!liff.isInitialized) {
    await liff.init({ liffId: liffId });
  }
  const profile = await liff.getProfile();
  return profile.userId;
}
