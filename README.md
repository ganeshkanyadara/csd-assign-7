# CSD Assignment 7: 10 Closest Locations Recommendation API

## Objective
Build a high-performance recommendation API that recommends the 10 closest locations matching a category within a circular radius from a dataset of 10,000 locations on a 1 × 1 grid, measured by actual road network grid traversal distance (shortest path) rather than straight-line Euclidean distance.

---

## API Specifications

- **Endpoint Route:** `/search/` (and `/search`)
- **Required Fields:** `(lat, long, cat, rad, link)`
- **HTTP Methods:** `GET` and `POST` (JSON body and Multipart form data)
- **Response:** JSON list of 10 recommended location IDs:
  ```json
  [5151, 5248, 5553, 4855, 5455, 4554, 5245, 5549, 5145, 5456]
  ```

### Input Parameters:
| Parameter | Type | Description |
|---|---|---|
| `lat` | float | Current Latitude ($0.0 \le lat \le 1.0$) |
| `long` | float | Current Longitude ($0.0 \le long \le 1.0$) |
| `cat` | string | Category to search (`bank`, `cafe`, `hospital`, `park`, `pharmacy`, `restaurant`, `school`, `store`) |
| `rad` | float | Search radius (circular Euclidean distance filter) |
| `link` | string / file | Linkage info: path to `link.txt`, filename, raw text, or uploaded file |

---

## Deployment Details

- **Host Machine:** `10.1.75.51`
- **Internal Container Port:** `6000`
- **Port Mapping:** `6000 + (2214 - 2000) = 6214`
- **External URL:** `http://10.1.75.51:6214/search/`
- **Internal / Local Container URL:** `http://127.0.0.1:6000/search/`

---

## Example Requests

### 1. GET Request
```bash
curl "http://10.1.75.51:6214/search/?lat=0.505051&long=0.505051&cat=hospital&rad=0.2&link=link.txt"
```

### 2. POST Request (JSON)
```bash
curl -X POST "http://10.1.75.51:6214/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 0.202020,
    "long": 0.303030,
    "cat": "pharmacy",
    "rad": 0.15,
    "link": "link.txt"
  }'
```

### 3. POST Request (Form Data / File Upload)
```bash
curl -X POST "http://10.1.75.51:6214/search/" \
  -F "lat=0.101010" \
  -F "long=0.101010" \
  -F "cat=bank" \
  -F "rad=0.25" \
  -F "link=@link.txt"
```

---

## Service Management (Inside Container)

On the container (`ssh -p 2214 student@10.1.75.51`):
```bash
cd /home/student/assign-7

# Check status
./status.sh

# Start daemon
./start.sh

# Stop daemon
./stop.sh

# Run tests
/opt/conda/bin/python3 -m unittest test_app.py test_service.py
```
