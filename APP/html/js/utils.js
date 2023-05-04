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

async function api_post(url, jsondata){
    // posts and returns raw response
    var base_url = detect_access_uri()+"/api";
    var url=base_url+url;

    try{
        let response = fetch(url, 
            {method:'POST', body:JSON.stringify(jsondata),
            headers: { "Content-type": "application/json; charset=UTF-8" }}
            );
        let res = await response;
        return res;
    }catch(err){
        console.log(err);
    }
}

async function api_get(url){
    var base_url = detect_access_uri()+"/api";
    var url=base_url+url;
    console.log("GET :", url);

    try{
        return fetch(url, {method:'GET'});
    }catch(err){
        console.log(err);
    }
}

function get_active_username(){
    return "superadmin";
}

function get_active_name(){
    return "SUPER ADMIN";
}
