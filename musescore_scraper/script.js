() => {
    let curPage = document.querySelector("main img");
    let scrollDiv = curPage.parentElement.parentElement;
    let classCounts = {};
    let desiredClass = undefined;
    for (let i = 0; i < scrollDiv.children.length; ++i) {
        let child = scrollDiv.children[i];
        let childClass = Array.from(child.classList).join(" ");
        if (!(childClass in classCounts)) {
            classCounts[childClass] = [];
        }
        classCounts[childClass].push(i);
        if (desiredClass === undefined
                || classCounts[childClass].length > classCounts[desiredClass].length) {
            desiredClass = childClass;
        }
    }

    let imgs = {};
    let curInd = classCounts[desiredClass][0];

    function myIndexOf(arr, ele) {
        for (let i = 0; i < arr.length; ++i) {
            if (arr[i] === ele) {
                return i;
            }
        }
        return -1;
    }

    return new Promise(resolve => {
        let observerArray = {};
        function addImg(ind) {
            return (records, observer) => {
                for (let record of records) { //records is a list of MutationRecords
                    console.log(ind, curInd);
                    if (record.target !== null
                        && record.target.tagName === "IMG"
                        && record.attributeName === "src"
                        && record.target.src)
                    {
                        if (!(ind in imgs)) {
                            imgs[ind] = record.target.src;
                        }
                        if (curInd == ind) {
                            if (ind == classCounts[desiredClass][classCounts[desiredClass].length - 1])
                            {
                                for (let observer of Object.values(observerArray)) {
                                    observer.disconnect();
                                }
                                let arr = Object.entries(imgs);
                                arr.sort((a, b) => { return Math.sign(a[0] - b[0]); });
                                resolve(arr.map((entry) => { return entry[1]; }));
                            }
                            else
                            {
                                ++curInd;
                                scrollDiv.scrollBy(0, record.target.height);
                                if (curInd == ind + 1) {
                                    addImg(curInd)([{
                                        attributeName: "src",
                                        target: scrollDiv.children[curInd].querySelector("img"),
                                    }], observerArray[curInd]);
                                }
                            }
                        }
                    }
                }
            };
        }
        for (let ind of classCounts[desiredClass]) {
            let observer = new MutationObserver(addImg(ind));
            observer.observe(scrollDiv.children[ind], {
                attributes: true,
                subtree: true,
            });
            observerArray[ind] = observer;
        }
        scrollDiv.scroll(0, 0);
        for (let ind of classCounts[desiredClass]){
            let img = scrollDiv.children[ind].querySelector("img");
            addImg(0)([{
                attributeName: "src",
                target: img,
            }], observerArray[ind]);
        }
    });
}
