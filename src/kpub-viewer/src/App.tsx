import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { handleTheme } from './theme'
import './App.css'
import { BooleanParam, useQueryParam, withDefault } from 'use-query-params'
// import { apiURL } from './config'
import { CssBaseline, ThemeProvider } from '@mui/material'
import { ArticleTable } from './article_table'
import { TopBar } from './top_bar'

export const apiURL = 'https://vm-dev-appserver/api/kpub'
export const keckURL = 'https://www.keckobservatory.org/'

export interface Snippits {
  [key: string]: {
    count: number
    snippets: string[]
  }
}

export interface Article {
  _id: string,
  title: string[]
  year: number
  instruments: string[]
  archive: '1' | '0' 
  bibcode: string
  abstract: string
  publisher?: string
  aff: string[]
  last_modifier: string
  date_modified: string
  month: number
  snippits: Snippits
  affiliation: string
  date: string
  alternate_bibcode?: string[]
  arxiv_class?: string[]
  author: string[],
  author_norm?: string[]
  database?: string[]
  doctype?: string
  doctype_facet_heir?: string[]
  doi?: string[]
  email?: string[]
  first_author?: string
  first_author_norm?: string
  id?: string
  recid?: number
  identifier?: string[]
  issue?: string
  keyword?: string[]
  keyword_facet?: string[]
  keyword_norm?: string[]
  keyword_schema?: string[]
  links_data?: string[]
  page?: string[]
  pub?: string
  pub_raw?: string
  pubdate?: string
  volume?: string
  read_count?: number
  cite_read_boost?: number
  classic_factor?: number
  reference: string[]
  property?: string[]
  citation_count?: number
  indexstamp?: string
  mission?: string
}

interface State {
  articles: Array<Article>
}

const StateContext = createContext<State | null>(null)
export const useStateContext = () => useContext(StateContext)

function App() {

  const [darkMode, setDarkMode] = useQueryParam('darkMode', withDefault(BooleanParam, true))

  const theme = useMemo(() => {
    const newTheme = handleTheme(darkMode)
    console.log('Theme:', newTheme)
    return newTheme
  }, [darkMode])

  const [state, setState] = useState<State>({} as State)



  useEffect(() => {

    const fetchData = async () => {
      const response = await fetch(`${apiURL}/getData`)
      if (!response.ok) {
        console.warn('Network response was not ok')
        //throw new Error('Network response was not ok')
      }
      else {
        const articles = await response.json()
        setState({
          articles: articles,
        })
        console.log('Fetched articles:', articles)
      }
    }
    // fetchData().catch((error) => {
    //   console.error('Error fetching data:', error)
    // })
  }, [])

  const handleThemeChange = () => {
    setDarkMode(!darkMode)
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <StateContext.Provider value={state}>
        <TopBar darkMode={darkMode} handleThemeChange={handleThemeChange} />
        <ArticleTable />
      </StateContext.Provider>
    </ThemeProvider>
  )
}

export default App
