//Requiere del Driver Node.js MongoDB 3.0.0+
var mongodb= require("mongodb");

var client= mongodb.MongoClient;
var url = "mongodb://localhost:27017/"

client.connect(url, function(err, client){
    var db= client.db("movie-dataset");
    var collection = db.collection("movies_metadata");

    var query={};

    var cursor = collection.find(query);

    cursor.forEach(
        function(doc){
            console.log(doc);
        },
        function(err){
            client.close();
        }
    );
});