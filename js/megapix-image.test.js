
function resizeImage(inputfile, outputcontainer) {
    document.getElementById(inputfile).onchange = function(e) {
        var file = e.target.files[0]
        var orientation;
        console.log("fil som ska laddas upp:" + inputfile);
        // MegaPixImage constructor accepts File/Blob object.
        var mpImg = new MegaPixImage(file);
        var testvar = 'test';
        // Render resized image into image element using quality option.
        // Quality option is valid when rendering into image element.
        var resImg = document.getElementById(outputcontainer);
        //get image orientation from EXIF library, then render image to 
        EXIF.getData(file, function() {
            orientation = EXIF.getTag(this, "Orientation");
            mpImg.render(resImg, testvar, { maxWidth: 300, maxHeight: 300, quality: 0.5, orientation: orientation });
            console.log("bildvinkel:" + orientation);

        });
    };

}

window.onload = function() {
    resizeImage('fileinput1','outputImage1');
    resizeImage('fileinput2','outputImage2');
    resizeImage('fileinput3','outputImage3');
    resizeImage('fileinput4','outputImage4');
    //resizeImage('fileinput5','outputImage5');

    
    document.getElementById('fileinput5').onchange = function(e) {
        var file = e.target.files[0]
        var orientation;
        // MegaPixImage constructor accepts File/Blob object.
        var mpImg = new MegaPixImage(file);

        // Render resized image into image element using quality option.
        // Quality option is valid when rendering into image element.
        var resImg = document.getElementById('outputImage5');
        //get image orientation from EXIF library, then render image to 
        EXIF.getData(file, function() {
            orientation = EXIF.getTag(this, "Orientation");
            mpImg.render(resImg, { maxWidth: 500, maxHeight: 500, quality: 0.5, orientation: orientation });
            console.log(orientation);

        });
    }; 
  
};


