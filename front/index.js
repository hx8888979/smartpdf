const api = "https://bmgq1lq4db.execute-api.us-west-2.amazonaws.com/prod/decryption"
const store = {};

async function onFileChange(event) {
    let file = null;
    if (event.type == "drop") {
        event.preventDefault();
        if (event.dataTransfer.files) {
            file = event.dataTransfer.files[0];
        } else {
            return;
        }
    } else {
        const ui = event.target;
        file = ui.files[0];
    }
    store.data.name = file.name;
    disabled();

    var reader = new FileReader();
    reader.onload = function () {
        const md5 = CryptoJS.algo.MD5.create();
        md5.update(CryptoJS.enc.Latin1.parse(reader.result));
        const digest = md5.finalize();
        store.data.md5 = digest.toString(CryptoJS.enc.Base64);
        console.log(store.data.md5);
        const req = new XMLHttpRequest();
        req.addEventListener("load", onPreSign);
        req.open("PUT", `${api}?md5=${store.data.md5}`);
        req.send();
        console.log("Presign requested");
    };
    showMain();
    reader.readAsBinaryString(file);
}

function onprogress(event) {
    if (event.lengthComputable) {
        var percentComplete = (event.loaded / event.total) * 100;
        store.ui.progressbar.setAttribute("aria-valuenow", percentComplete);
        store.ui.progressbar.style.width = `${percentComplete}%`;
    }
}

function onPreSign() {
    if (this.status >= 200 && this.status < 300) {
        const responseBody = JSON.parse(this.responseText)
        const { url, fields: { key, AWSAccessKeyId: awsAccessKeyId, "x-amz-security-token": xAmzSecurityToken, policy, signature } } = responseBody;

        const formData = new FormData();
        formData.append("key", key);
        formData.append("Policy", policy);
        formData.append("Content-MD5", store.data.md5);
        formData.append("x-amz-meta-name", store.data.name);

        formData.append("AWSAccessKeyId", awsAccessKeyId);
        formData.append("x-amz-security-token", xAmzSecurityToken);
        formData.append("X-Amz-Signature", signature);
        formData.append("Signature", signature);

        formData.append("file", store.ui.pdfFileInput.files[0]);

        const req = new XMLHttpRequest();
        req.open('POST', url);
        req.upload.onprogress = onprogress;
        req.onload = onUpload;
        req.send(formData);
    } else {
        showError();
    }
}

function onUpload() {
    if (this.status >= 200 && this.status < 300) {
        console.log("uploaded");
        store.ui.status.innerText = "Processing...";
        store.ui.progressbar.className = "progress-bar progress-bar-striped bg-info progress-bar-animated";
        store.data.retry = 0;
        store.data.retry2 = 0;
        setTimeout(updateStatus, 2000);
    } else {
        showError();
    }
}

function updateStatus() {
    const req = new XMLHttpRequest();
    req.open('Get', `${api}?md5=${store.data.md5}`);
    req.onload = () => {
        if (req.status == 200) {
            const { status, s3 } = JSON.parse(req.responseText);
            switch (status) {
                case "InProcessing":
                    store.data.retry += 1
                    break;
                case "Done":
                    store.ui.status.innerText = "Done, Please click Download button";
                    store.ui.progressbar.className = "progress-bar progress-bar-striped bg-success";
                    store.ui.download.href = s3;
                    store.ui.download.classList.remove("disabled");
                    return;
                case "Error":
                    store.ui.status.innerHTML = `Something Wrong, Please Contact XGG<br/>Code: ${store.data.md5}`;
                    store.ui.progressbar.className = "progress-bar progress-bar-striped bg-danger";
                    return;
            }
        } else if (req.status == 404) {
            store.data.retry2 += 1
        } else {
            store.data.retry2 = 4; // DO NOT Retry
        }

        if (store.data.retry <= 60 && store.data.retry2 <= 6) {
            setTimeout(updateStatus, 5000);
        } else {
            showError();
        }
    };
    req.send();
}

function disabled() {
    store.ui.pdfFileInput.disabled = true;
    store.ui.dropText.classList.add("d-none");
    store.ui.dropArea.removeEventListener('drop', onFileChange);
}

function showError() {
    disabled();
    showMain();
    store.ui.status.innerHTML = "Something Wrong, Please try again";
    store.ui.progressbar.className = "progress-bar progress-bar-striped bg-danger";
}

function showMain() {
    store.ui.main.classList.remove("d-none");
}

function init() {
    store.ui = {
        pdfForm: document.getElementById('pdf-uploader'),
        pdfFileInput: document.getElementById('pdf-file'),
        progressbar: document.getElementById('progress'),
        status: document.getElementById('status'),
        download: document.getElementById('download'),
        dropArea: document.getElementById('drop-area'),
        dropText: document.getElementById('drop-text'),
        main: document.getElementById('main'),
    };
    store.data = {}

    store.ui.pdfFileInput.addEventListener('change', onFileChange);
    store.ui.pdfFileInput.addEventListener('click', (event) => event.stopPropagation());
    store.ui.dropArea.addEventListener('drop', onFileChange);
    store.ui.dropArea.addEventListener('dragover', (event) => event.preventDefault());
    store.ui.dropArea.addEventListener('click', () => store.ui.pdfFileInput.click());

    console.log("Init finished");
}

init();
