export interface Experience {
  id: string
  title: string
  company: string
  location: {
    city: string
    country: string
    lat: number
    lng: number
    isRemote: boolean
  }
  startDate: string
  endDate: string
  color: "pink" | "yellow" | "green" | "blue"
}

export const experiences: Experience[] = [
  {
    id: "1",
    title: "Indo-Gangetic Plains",
    company: "Wheat & Rice Belt",
    location: {
      city: "Ludhiana",
      country: "India",
      lat: 30.901,
      lng: 75.8573,
      isRemote: false,
    },
    startDate: "2020-01-15",
    endDate: "2024-12-27",
    color: "yellow",
  },
  {
    id: "2",
    title: "Deccan Plateau",
    company: "Cotton & Pulses Zone",
    location: {
      city: "Pune",
      country: "India",
      lat: 18.5204,
      lng: 73.8567,
      isRemote: false,
    },
    startDate: "2020-06-20",
    endDate: "2024-12-27",
    color: "pink",
  },
  {
    id: "3",
    title: "Cauvery Delta",
    company: "Rice & Sugarcane Zone",
    location: {
      city: "Thanjavur",
      country: "India",
      lat: 10.787,
      lng: 79.1378,
      isRemote: false,
    },
    startDate: "2021-03-10",
    endDate: "2024-12-27",
    color: "green",
  },
  {
    id: "4",
    title: "Eastern Rice Belt",
    company: "Rice & Jute Zone",
    location: {
      city: "Kolkata",
      country: "India",
      lat: 22.5726,
      lng: 88.3639,
      isRemote: false,
    },
    startDate: "2021-09-05",
    endDate: "2024-12-27",
    color: "blue",
  },
  {
    id: "5",
    title: "Southern Plateau",
    company: "Millets & Coffee Zone",
    location: {
      city: "Bengaluru",
      country: "India",
      lat: 12.9716,
      lng: 77.5946,
      isRemote: false,
    },
    startDate: "2022-02-18",
    endDate: "2024-12-27",
    color: "pink",
  },
]
