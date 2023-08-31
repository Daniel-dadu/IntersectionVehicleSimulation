// Not completely sure if the code is completed
// The final version of this code must be inside PaqueteFinalReto.unitypackage

using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

[System.Serializable]

class AgentAtributes
{
    public float x;
    public float y;
    public int dir;
}
class MyCar
{
    public List<AgentAtributes> cars;

    override public string ToString()
    {
        string s = "";
        foreach(AgentAtributes car in cars)
        {
            s += "[" + car.x + ", " + car.y + "] - ";
        }
        return s;
    }
}

public class CarMovement : MonoBehaviour
{

    GameObject[] agents;
    public GameObject carroMorado;

    string simulationURL = null;
    int numOfAgents = 20; // Hardcoded porque no lo puedo mandar desde el ConnectToMesa

    // Start is called before the first frame update
    void Start()
    {
        StartCoroutine(ConnectToMesa());

        agents = new GameObject[numOfAgents];
        for (int i = 0; i < numOfAgents; i++){
            agents[i] = Instantiate(carroMorado, Vector3.zero, Quaternion.identity);
        }

    }

    IEnumerator ConnectToMesa()
    {
        WWWForm form = new WWWForm();

        using (UnityWebRequest www = UnityWebRequest.Post("http://localhost:5000/games", form))
        {
            yield return www.SendWebRequest();

            if (www.result != UnityWebRequest.Result.Success)
            {
                Debug.Log(www.error);
            }
            else
            {
                simulationURL = www.GetResponseHeader("Location");
                // Funciona pero no lo lee a tiempo
                numOfAgents = int.Parse(www.GetResponseHeader("NumOfAgents"));

                Debug.Log("Connected to simulation through Web API");
                Debug.Log(simulationURL);
            }
        }
    }

    IEnumerator UpdatePositions()
    {
        using (UnityWebRequest www = UnityWebRequest.Get(simulationURL))
        {
            if (simulationURL != null)
            {
                // Request and wait for the desired page.
                yield return www.SendWebRequest();

                Debug.Log(www.downloadHandler.text);
                Debug.Log("Data has been processed");
                MyCar myCars = JsonUtility.FromJson<MyCar>(www.downloadHandler.text);
                Debug.Log(myCars.ToString());

                for(int i = 0; i < agents.Length; i++)
                {
                    agents[i].transform.position = new Vector3(myCars.cars[i].x, 0, myCars.cars[i].y);
                    Debug.Log("Agent" + i + "in pos: " + agents[i].transform.position);
                }
            }
        }
    }

    // Update is called once per frame
    void Update() {
        StartCoroutine(UpdatePositions());
    }
}