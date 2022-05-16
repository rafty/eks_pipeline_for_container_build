import os
import boto3
from flask import Flask
from flask import jsonify
from flask import request

app = Flask(__name__)

dynamo_client = boto3.client('dynamodb', region_name='ap-northeast-1')
table_name = 'musicTable'


@app.route('/')
def hello():
    return 'Hello World!'


@app.route('/v1/music/90s/<string:artist>')
def get_artist(artist):
    resp = dynamo_client.get_item(
        TableName=table_name,
        Key={
            'artist': {'S': artist}
        }
    )
    item = resp.get('Item')
    if not item:
        return jsonify({'error': 'Artist does not exist'}), 404

    return jsonify({
        'artist': item.get('artist').get('S'),
        'song': item.get('song').get('S')
    })


@app.route('/v1/music/90s', methods=['POST'])
def create_artist():
    artist = request.json.get('artist')
    song = request.json.get('song')
    if not artist or not song:
        return jsonify({'error': 'Please provide Artist and Song'}), 400

    resp = dynamo_client.put_item(
        TableName=table_name,
        Item={
            'artist': {'S': artist},
            'song': {'S': song}
        }
    )

    return jsonify({
        'artist': artist,
        'song': song
    })


if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=8080, debug=True)
