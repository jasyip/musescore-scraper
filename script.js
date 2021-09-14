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
        if (desiredClass === undefined || classCounts[childClass].length > classCounts[desiredClass].length) {
            desiredClass = childClass;
        }
    }
    // console.log(classCounts[desiredClass])
    let svgs = [];
    let i = undefined;

    scrollDiv.scroll({
        left : 0,
        top : 0,
        behavior : "smooth"
    });
    
    return new Promise(resolve => {
        function addSvg(records, observer) {
            for (let record of records) { //records is a list of MutationRecords
                if (record.target.tagName === "IMG"
                    && record.attributeName === "src"
                    && record.target.src !== undefined)
                {
                    svgs.push(record.target.src);
                   
                    if (classCounts[desiredClass].indexOf(record.target.parentElement)
                        == classCounts[desiredClass].length - 1)
                    {
                        console.log("DONE!");
                        observer.disconnect();
                        resolve(svgs);
                    }
                    scrollDiv.scrollBy(0, record.target.height);
                    /*
                    else
                    {
                        scrollDiv.scrollBy(0, img.height);
                    }
                    break;
                    */
                    break;
                }
            }
        }
        let observer = new MutationObserver(addSvg);
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
            addSvg([{
                attributeName: "src",
                target: classCounts[desiredClass][0].querySelector("img"),
            }]);
        }
    });
    /*
    return { svgs : new Promise((resolve, reject) => {
        setTimeout(function() {
            for (let i = 0; i < classCounts[desiredClass].length; ++i) {
                setTimeout(function() {
                    let img = classCounts[desiredClass][i].querySelector("img");
                    svgs.push(img.src);
                    scrollDiv.scrollBy({
                        left: 0,
                        top: img.height,
                        behavior: 'smooth'
                    });
                }, 2000 * i);
            }
            setTimeout(resolve, classCounts[desiredClass].length * 2000, svgs);
        }, 2000);
    })};
    */
}
