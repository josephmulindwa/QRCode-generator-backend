function get_api_uri(){
    return "http://localhost/qrcode-generator/index.php";
}

async function test_url(url){
    // checks if url is collectable
    try{
        fetch(url, {method:"GET"});
        return true;
    }catch(err){
        return false;
    }
}

function validate_string(value){
    if (value!==undefined && value!==null && value.length!==0){
        return true;
    }
    return false;
}

function detect_access_uri(){
    // returns the base url
    var uri = window.location.href;
    if (!uri.startsWith("http")){
        return null;
    }
    var splitted = uri.split("//");
    if(splitted.length<2){
        return null;
    }
    var final = splitted[0]+"//"+splitted[1].split("/")[0];
    
    return final;
}


function get_app_name(){
    return "QRGEN";
}

function set_storage_item(key, val){
    sessionStorage.setItem(key, val);
}

function get_storage_item(key){
    return sessionStorage.getItem(key);
}

function clear_storage(){
    sessionStorage.clear();
}

async function api_post(url, data){
    // posts and returns raw response
    var base_url = get_api_uri();
    var url=base_url+url;
    let token = get_storage_item("token");

    try{
        let response = fetch(url, 
            {
                method:'POST', 
                body:data,
                headers: {"Authorization":"bearer "+token}
            }
            );
        let res = await response;
        return res;
    }catch(err){
        console.log(err);
    }
}

async function api_get(url){
    var base_url = get_api_uri();
    var url=base_url+url;
    console.log("GET :", url);
    let token = get_storage_item("token");

    try{
        return fetch(url, {
            method:'GET',
            headers:{"Authorization":"bearer "+token}
        });
    }catch(err){
        console.log(err);
    }
}

function get_active_username(){
    let username = get_storage_item("username");
    console.log("@active_username :", username);
    if (!validate_string(username)){
        return "";
    }
    return username;
}

function get_active_name(){
    let name = get_storage_item("name");
    if (!validate_string(name)){
        return "";
    }
    return name;
}

function go_to_profile(){
    var username = get_active_username();
    set_storage_item("user-name", username);
    window.location.href = "profile.html";
    return true;
}

async function get_user_permissions(){
    var username = get_active_username();
    if (username!==null && username.length>0){
        let res = await api_get("/user/permissions?username="+username);
        let datajs = await res.json();
        if (datajs["status"]==="success"){
            var permissions = JSON.stringify(datajs["data"]);
            set_storage_item("permissions", permissions);
            return permissions;
        }
    }
    return [];
}

function get_page_limit(){
    return 15; //.env
}
