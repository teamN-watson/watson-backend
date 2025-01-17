export function getProfilePhotoUrl(photo) {
    if (!photo) return '/static/images/default_profile.png'; // 기본 이미지

    const photoParts = photo.split("/").splice(2); // URL 파싱

    if (photoParts[0] === "items") {
        return `https://cdn.fastly.steamstatic.com/steamcommunity/public/images/${photoParts.join("/")}`;
    } else if (photoParts[0] === "https%3A") {
        return decodeURIComponent(photoParts.join("/"));
    } else {
        return photo;
    }
}
