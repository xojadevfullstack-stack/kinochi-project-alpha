const url = "https://youtu.be/UPFRltMOgPo?si=Bg45mA6X0LRNhm6S";
const url2 = "https://youtu.be/UPFRItMOgPo?si=ixXu0Ovyk7DlFd5M";
const getYoutubeId = (url) => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return match && match[2].length === 11 ? match[2] : null;
};
console.log("url1:", getYoutubeId(url));
console.log("url2:", getYoutubeId(url2));
