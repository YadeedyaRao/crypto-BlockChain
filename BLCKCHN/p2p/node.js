const WS = require("ws")

const PORT = 3000;
const PEERS = [];
const MY_ADDRESS = "ws://localhost:3000";
const server = new WS.server({port : PORT});

let opened = [], connected = [];



console.log("Listening on PORT", PORT);

server.on("connection", async (socket, req)=>{
    socket.on("message", message =>{
        const _message = JSON.parse(message)

        switch(_message.type){
            case "TYPE_HANDSHAKE":
                const nodes = _message.data;

                nodes.forEach(node => connect(node))
        }
    })
})

async function connect(address){
    if (!connected.find(peerAddress => peerAddress === address) && address !== MY_ADDRESS){
        const socket = new WS(address);

        socket.on("open", () => {
            socket.send(JSON.stringify(produceMessage("TYPE_HANDSHAKE", [MY_ADDRESS, ...connected])))

            opened.forEach(node => node.select.send(JSON.stringify(produceMessage("TYPE_HANDSHAKE", [address]))))

            
            if(!opened.find(peerAddress => peerAddress === address) && address !== MY_ADDRESS){
                opened.push({socket, address});
            }

            if(!connected.find(peerAddress => peerAddress === address) && address !== MY_ADDRESS){
                connected.push({socket, address});
            }
        })

        socket.on("close", ()=>{
            opened.splice(connected.indexOf(address), 1);
            connected.splice(connected.indexOf(address), 1);
        })
    }
}

function produceMessage(type, data){
    return {type, data};
}

process.on("uncaughtException", err => console.log(err));

PEERS.forEach(peer => connect(peer))