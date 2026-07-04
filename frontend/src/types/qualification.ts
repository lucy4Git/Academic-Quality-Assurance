export interface SubjectEntry {
  name: string;
  credits: number;
  percentage: number;
  semester: number;
}

export interface CalculationRequest {
  student_name: string;
  institution_name: string;
  programme_name: string;
  qualification_type: string;
  nqf_level_claimed?: number | null;
  academic_year?: string | null;
  entries: SubjectEntry[];
  notes?: string | null;
}

export interface SubjectResult {
  name: string;
  credits: number;
  percentage: number;
  letter_grade: string;
  grade_points: number;
  quality_points: number;
  semester: number;
  passed: boolean;
}

export interface SemesterGPA {
  semester: number;
  gpa: number;
  credits: number;
  subjects: number;
}

export interface NQFAdvisory {
  advisory_level: number;
  advisory_label: string;
  qualification_type_advisory: string;
  minimum_credits: number;
  actual_credits: number;
  credit_gap: number;
  advisory_note: string;
}

export interface CalculationResult {
  student_name: string;
  institution_name: string;
  programme_name: string;
  qualification_type: string;
  academic_year: string | null;
  subjects: SubjectResult[];
  total_credits: number;
  total_quality_points: number;
  gpa: number;
  cgpa: number;
  passed_subjects: number;
  failed_subjects: number;
  pass_rate: number;
  semesters: SemesterGPA[];
  nqf_advisory: NQFAdvisory;
  advisory_summary: string;
  advisory_warnings: string[];
  advisory_recommendations: string[];
  disclaimer: string;
}

export interface QualificationRecordBrief {
  id: string;
  student_name: string;
  institution_name: string;
  programme_name: string;
  qualification_type: string;
  academic_year: string | null;
  total_credits: number;
  gpa: number;
  cgpa: number | null;
  nqf_advisory_level: number | null;
  nqf_advisory_label: string | null;
  created_at: string;
}

export interface QualificationRecordDetail extends QualificationRecordBrief {
  entries: SubjectEntry[];
  calculation_result: CalculationResult;
  notes: string | null;
}
