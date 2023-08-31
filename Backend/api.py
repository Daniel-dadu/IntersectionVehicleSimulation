from flask import Flask, jsonify
import uuid
import os

from cars import Street

games = {}

app = Flask(__name__, static_url_path='')

port = int(os.getenv('PORT', 8000))

@app.route("/reto", methods=["POST"])
def create():
    global games
    id = str(uuid.uuid4())
    games[id] = Street()
    return "ok", 201, {'Location': f"/reto/{id}"}


@app.route("/reto/<id>", methods=["GET"])
def queryState(id):
    global model
    model = games[id]
    model.step()
    cars = []
    signals = []
    pedestrians = []

    for agent in model.schedule.agents:
        if(str(type(agent).__name__) == "Signal"):
            signals.append({
                "x": float(agent.pos[0]), 
                "y": float(agent.pos[1]), 
                "color": agent.light
            })
        elif(str(type(agent).__name__) == "Car"):
            cars.append({
                "x": float(agent.pos[0]), 
                "y": float(agent.pos[1]), 
                "dir": int(agent.direction)
            })
        else:
            pedestrians.append({
                "x": float(agent.pos[0]), 
                "y": float(agent.pos[1]), 
                "dir": int(agent.direction),
                "stopped": agent.stopped
            })

    return jsonify({
        "cars": cars,
        "signals": signals,
        "pedestrians": pedestrians
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)