from flask import Flask, redirect, render_template, request, url_for
from time import strftime
import sqlite3

app = Flask(__name__)


@app.route("/")
@app.route("/home")
def index():
    return render_template("index.html")


connect = sqlite3.connect("robici.db")
connect.execute("PRAGMA foreign_keys = ON")
connect.execute(
    """
    CREATE TABLE IF NOT EXISTS robota (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                       robic INTEGER NOT NULL, datum TEXT NOT NULL,
                                       prichod TEXT NOT NULL,
                                       odchod TEXT,
                                       FOREIGN KEY (robic) REFERENCES robic(id),
                                       CHECK (odchod IS NULL OR odchod > prichod))
    """
)
connect.execute(
    """
    CREATE TABLE IF NOT EXISTS robic (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                      meno TEXT)
    """
)


@app.route("/list", methods=["GET"])
def robici():
    connect = sqlite3.connect("robici.db")
    cursor = connect.cursor()
    id = request.args.get("rmid")
    if id is not None:
        cursor.execute("DELETE FROM robota WHERE id = ?", (id,))
        connect.commit()
    start = request.args.get("start", strftime("%Y-%m-01"))
    end = request.args.get("end", strftime("%Y-%m-%d"))
    cursor.execute(
        """
        SELECT
            meno,
            printf('%d:%02d', monsek / 3600, (monsek % 3600) / 60) AS mesiac,
            printf('%d:%02d', satsek / 3600, (satsek % 3600) / 60) AS soboty,
            printf('%d:%02d', sunsek / 3600, (sunsek % 3600) / 60) AS nedele
        FROM
            (SELECT
                meno,
                sum(unixepoch(odchod) - unixepoch(prichod)) AS monsek,
                sum(CASE WHEN strftime('%u', datum) = '6' THEN unixepoch(odchod) - unixepoch(prichod) END) AS satsek,
                sum(CASE WHEN strftime('%u', datum) = '7' THEN unixepoch(odchod) - unixepoch(prichod) END) AS sunsek
            FROM
                robota
                JOIN
                robic ON robota.robic = robic.id 
            WHERE
                strftime("%Y-%m-%d", datum) BETWEEN strftime("%Y-%m-%d", ?) AND strftime("%Y-%m-%d", ?)
            GROUP BY robic.id)
        ORDER BY
            monsek
        """,
        (start, end),
    )
    data = cursor.fetchall()
    cursor.execute(
        """
        SELECT
            robota.id, meno,
            datum, prichod,
            odchod
        FROM
            robota
            JOIN
            robic ON robota.robic = robic.id
        WHERE
            strftime("%Y-%m-%d", datum) BETWEEN strftime("%Y-%m-%d", ?) AND strftime("%Y-%m-%d", ?)
        ORDER BY
            datum DESC, prichod DESC, odchod DESC
        """,
        (start, end),
    )
    zrobene = cursor.fetchall()
    return render_template(
        "list.html", data=data, zrobene=zrobene, start=start, end=end
    )


@app.route("/praca", methods=["GET", "POST"])
def praca():
    connect = sqlite3.connect("robici.db")
    cursor = connect.cursor()
    if request.method == "GET":
        id = request.args.get("id")
        start = request.args.get("start")
        end = request.args.get("end")
        cursor.execute("SELECT * FROM robic")
        nahmen = cursor.fetchall()
        if id is not None:
            cursor.execute(
                """
                SELECT
                    robic, datum, prichod, odchod
                FROM
                    robota
                WHERE
                    id = ?
                """,
                (id,),
            )
            data = cursor.fetchone()
            return render_template(
                "praca.html", nahmen=nahmen, data=data, id=id, start=start, end=end
            )

        return render_template("praca.html", nahmen=nahmen)

    else:
        id = request.form.get("id")
        start = request.form.get("start")
        end = request.form.get("end")
        meno = request.form["meno"]
        datum = request.form["datum"]
        prichod = request.form["prichod"]
        odchod = request.form["odchod"]
        odchod = odchod if odchod != "" else "NULL"

        if id is not None:
            cursor.execute(
                """
                UPDATE
                    robota
                SET
                    robic = ?,
                    datum = ?,
                    prichod = ?,
                    odchod = ?
                WHERE
                    id = ?
                """,
                (meno, datum, prichod, odchod, id),
            )
            connect.commit()
            return redirect(url_for("robici", start=start, end=end))
        else:
            cursor.execute(
                """
                INSERT INTO
                    robota (robic, datum, prichod, odchod)
                VALUES
                    (?,?,?,?)
                """,
                (meno, datum, prichod, odchod),
            )
            connect.commit()
            return redirect(url_for("praca"))


@app.route("/registracia", methods=["POST", "GET"])
def registracia():
    connect = sqlite3.connect("robici.db")
    cursor = connect.cursor()
    if request.method == "POST":
        meno = request.form["meno"]
        cursor.execute("INSERT INTO robic (meno) VALUES (?)", (meno,))
        connect.commit()
    return render_template("registracia.html")


if __name__ == "__main__":
    app.run()  # debug=False, host="0.0.0.0")
