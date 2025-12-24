"use client";

import { useEffect, useState } from "react";

// for later use
function parse(num) {
  switch (num) {
    case 1001:
      return "+";
    case 1002:
      return "-";
    case 1003:
      return "*";
    case 1004:
      return " ";
    default:
      return num.toString();
  }
}

function Game({ curGame }) {

  return (
    <div>
      {curGame.grid}
    </div>  
  )
}

export default function Solo() {
  const [game, setGame] = useState(null);

  useEffect(() => {
    fetch("/api/solo", {
      credentials: "include"
    })
      .then((res) => res.json())
      .then((data) => setGame(data))
      .catch((err) => console.error(err));
    }, []);

  if (!game) {
    return <p>Loading game...</p>;
  }

  return (
    <>
      <Game curGame={game}/>
    </>
  );
}
  
/*
return (
  <div style={styles.container}>
    <h1 style={styles.title}>67! Game Mock</h1>

    <div
      style={{
        ...styles.grid,
        width: COLS * TILE_SIZE,
        height: ROWS * TILE_SIZE,
      }}
    >
      <AnimatePresence>
        {grid.map((row, r) =>
          row.map((tile, c) => (
            <motion.div
key={`${r}-${c}-${tile.id}`} // now guaranteed unique
layout
initial={{ scale: 0.8, opacity: 0 }}
animate={{ scale: 1, opacity: 1 }}
exit={{ scale: 0.5, opacity: 0 }}
transition={{ type: "spring", stiffness: 300, damping: 30 }}
style={{
  ...styles.tile,
  backgroundColor: OPERATORS.includes(tile.value)
    ? "#0af"
    : tile.value === "_"
    ? "#ccc"
    : "#f0a",
  color: tile.value === "_" ? "#888" : "white",
}}
>
{tile.value === "_" ? "" : tile.value}
</motion.div>

          ))
        )}
      </AnimatePresence>
    </div>

    <div style={styles.controls}>
      <button onClick={() => move("up")} style={styles.button}>
        Up
      </button>
      <div style={{ marginTop: 8 }}>
        <button onClick={() => move("left")} style={styles.button}>
          Left
        </button>
        <button
          onClick={() => move("right")}
          style={{ ...styles.button, marginLeft: 8 }}
        >
          Right
        </button>
      </div>
      <button
        onClick={() => move("down")}
        style={{ ...styles.button, marginTop: 8 }}
      >
        Down
      </button>
    </div>
  </div>
)
*/


  /*
const styles = {
  container: { padding: 20, textAlign: "center" },
  title: { fontSize: 32, marginBottom: 20 },
  grid: {
    display: "grid",
    gridTemplateRows: `repeat(${ROWS}, ${TILE_SIZE}px)`,
    gridTemplateColumns: `repeat(${COLS}, ${TILE_SIZE}px)`,
    gap: 6,
    justifyContent: "center",
    marginBottom: 20,
    position: "relative",
  },
  tile: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
    border: "1px solid #ccc",
    fontSize: 24,
    fontWeight: "bold",
    boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
    width: TILE_SIZE,
    height: TILE_SIZE,
  },
  controls: { marginTop: 20 },
  button: {
    padding: "10px 20px",
    fontSize: 18,
    borderRadius: 6,
    border: "none",
    backgroundColor: "#0070f3",
    color: "white",
    cursor: "pointer",
  },
};*/
