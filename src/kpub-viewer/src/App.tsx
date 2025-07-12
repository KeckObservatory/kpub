import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { handleTheme } from './theme'
import { StringParam, useQueryParam, withDefault } from 'use-query-params'
import { apiURL } from './config'
import { CssBaseline, ThemeProvider } from '@mui/material'
import { ArticleTable } from './article_table'
import { TopBar } from './top_bar'
import { Box } from '@mui/material'

//export const apiURL = 'http://vm-dev-appserver/api/kpub'

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
  articles: Array<Article>,
}

interface StateContextType {
  articles: Array<Article>
  setArticles: (articles: Array<Article>) => void
  isAdmin: React.RefObject<boolean | null>
}

const StateContext = createContext<StateContextType | null>(null)
export const useStateContext = () => useContext(StateContext)

function App() {

  // const [darkMode, setDarkMode] = useQueryParam('darkMode', withDefault(BooleanParam, true))
  const [monthyear, _] = useQueryParam('monthyear', withDefault(StringParam, new Date().getFullYear().toString()))

  const darkMode = false

  const theme = useMemo(() => {
    const newTheme = handleTheme(darkMode)
    console.log('Theme:', newTheme)
    return newTheme
  }, [darkMode])

  const [state, setState] = useState<State>({} as State)
  const isAdmin = useRef<boolean | null>(null);

  const fetchData = async () => {
    const response = await fetch(`${apiURL}/get_table?monthyear=${monthyear}`)
    if (!response.ok) {
      console.warn('Network response was not ok')
      throw new Error('Network response was not ok')
    }
    else {
      const resp = await response.json()
      if (isAdmin.current === null) {
        isAdmin.current = resp.isAdmin
      }
      setState((prevState) => {
        return {
          ...prevState,
          articles: resp.articles,
        }
      })
      console.log('Fetched articles:', resp.articles)
    }
  }

  useEffect(() => {
    fetchData().catch((error) => {
      console.error('Error fetching data using default:', error)
    })
  }, [monthyear])

  // const handleThemeChange = () => {
  //   setDarkMode(!darkMode)
  // }

  const stateContext = {
    isAdmin: isAdmin,
    articles: state.articles,
    setArticles: (articles: Array<Article>) => {
      setState((prevState) => ({
        ...prevState,
        articles: articles,
      }))
    }
  }

  return (
    <div className="App" style={{
      "maxWidth": isAdmin.current ? "1900px" : "1430px",
      "margin": "0 auto",
      "padding": "2rem",
      "textAlign": "center",
    }}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <StateContext.Provider value={stateContext}>
          {/* <TopBar darkMode={darkMode} handleThemeChange={handleThemeChange} /> */}
          <TopBar />
          <Box
            sx={{
              height: 1000,
              width: '100%',
            }}
          >
            <ArticleTable articles={state.articles} isAdmin={isAdmin.current}/>
          </Box>
        </StateContext.Provider>
      </ThemeProvider>
    </div>
  )
}

export default App
