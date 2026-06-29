export type CategoryKeywordRule = {
  category: string;
  keywords: string[];
};

export const CATEGORY_KEYWORDS: CategoryKeywordRule[] = [
  { category: 'EMI',           keywords: ['emi','loan','instalment','installment','car loan','home loan','bike loan','personal loan','education loan','credit card emi','no cost emi','bajaj finserv','car','bike','vehicle','two-wheeler','auto loan'] },
  { category: 'Insurance',     keywords: ['insurance','premium','lic','term plan','mediclaim','health insurance','car insurance','bike insurance','policy','star health','hdfc life','bajaj allianz','max life','tata aia'] },
  { category: 'Savings',       keywords: ['rd','recurring deposit','fd','fixed deposit','ppf','savings','piggy','emergency fund','chit fund'] },
  { category: 'Investments',   keywords: ['sip','nps','elss','mutual fund','stocks','shares','zerodha','groww','kuvera','coin','demat','investment'] },
  { category: 'Utilities',     keywords: ['electricity','water','gas','internet','broadband','wifi','postpaid','mobile bill','jio','airtel','bsnl','vi ','bescom','tangedco','piped gas','landline'] },
  { category: 'Housing',       keywords: ['rent','maintenance','society','pg','hostel','flat','apartment','hoa','strata'] },
  { category: 'Household',     keywords: ['maid','cook','driver','nanny','bai','dhobi','laundry','helper','housekeeper','cleaning','watchman','security','garbage'] },
  { category: 'Entertainment', keywords: ['netflix','spotify','prime','hotstar','disney','youtube premium','zee5','sonyliv','gym','fitness','subscription','membership','cult.fit','apple one'] },
  { category: 'Course',        keywords: ['tuition','coaching','school fees','college fees','course','udemy','coursera','unacademy','byju','fees'] },
];

export function suggestCategory(billName: string): string | null {
  const lower = billName.toLowerCase().trim();
  if (!lower) return null;
  for (const rule of CATEGORY_KEYWORDS) {
    for (const kw of rule.keywords) {
      if (lower.includes(kw)) return rule.category;
    }
  }
  return null;
}
