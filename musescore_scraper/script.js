() => {
    let curPage = document.querySelector("main img");
    let scrollDiv = curPage.parentElement.parentElement;
    let classCounts = {};
    let desiredClass = undefined;
    for (let child of scrollDiv.children) {
        let childClass = Array.from(child.classList).join(" ");
        if (!(childClass in classCounts)) {
            classCounts[childClass] = [];
        }
        classCounts[childClass].push(child);
        if (desiredClass === undefined
                || classCounts[childClass].length > classCounts[desiredClass].length) {
            desiredClass = childClass;
        }
    }

    //If it's 2 pages, the 2nd page may be already loaded, thus making generic function not work.
    if (classCounts[desiredClass].length <= 2) {
        let imgs = [];
        for (let div of classCounts[desiredClass]) {
            img = div.querySelector("img");
            if (img !== undefined) {
                imgs.push(img.src);
            }
        }
        if (imgs.length == classCounts[desiredClass].length) {
            return imgs;
        }
    }

    let imgs = [];
    let i = undefined;

    scrollDiv.scroll({
        left : 0,
        top : 0,
    });
    
    return new Promise(resolve => {
        function addImg(records, observer) {
            for (let record of records) { //records is a list of MutationRecords
                if (record.target.tagName === "IMG"
                    && record.attributeName === "src"
                    && record.target.src !== undefined)
                {
                    imgs.push(record.target.src);
                   
                    if (classCounts[desiredClass].indexOf(record.target.parentElement)
                        == classCounts[desiredClass].length - 1)
                    {
                        observer.disconnect();
                        resolve(imgs);
                    }
                    else
                    {
                        scrollDiv.scrollBy(0, record.target.height);
                    }
                    break;
                }
            }
        }
        let observer = new MutationObserver(addImg);
        for (let child of classCounts[desiredClass]) {
            observer.observe(child, {
                attributes: true,
                subtree: true,
            });
        }
        if (classCounts[desiredClass][0].children.length === 0) {
            divScroll.scroll(0, 0);
        }
        else
        {
            addImg([{
                attributeName: "src",
                target: classCounts[desiredClass][0].querySelector("img"),
            }]);
        }
    });
}
