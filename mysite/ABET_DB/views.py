from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.template import loader
from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from django.views.generic import TemplateView
from django.core.serializers.json import DjangoJSONEncoder
from django.core.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
#from django.utils import timezone
from sets import Set
from ABET_DB.exceptions import ABET_Error

from ABET_DB.models import *
from django.http import HttpResponse, JsonResponse

'''
def current():
    now = timezone.now()
    semNow = str()
    if now.month <= 5:
        semNow = "spring"
    elif now.month >= 7:
        semNow = "fall"
    else:
        semNow = "summer"
   
    return (semNow, now.year)
'''


def professorPage(request):
    # after HARRY figures out security, this wont be needed
    # this should be passed in upon login
    request.session['netid'] = 'jkohann' 
    professorNetID = request.session['netid']
    
    sectionList = sections.objects.filter(professor__netID=professorNetID)
    
    # make a list of all semesters
    semesterSet = Set()
    for s in sectionList:
        syStr = s.semester +' '+ str(s.year)
        semesterSet.add(syStr)

    nowSem, nowYear = current()
    sectionsNow = sectionList.filter(semester=nowSem, year=nowYear)
    
    perfLevList = performanceLevels.objects.all()

    # run the template
    template = loader.get_template('ABET_DB/prof.html')
    context = {
        'netid':professorNetID,
        'semesters':list(semesterSet),
        'currentSem':nowSem +' '+ str(nowYear),
        'courses':sectionsNow,
        'perfLevels':perfLevList,
    }
    return HttpResponse(template.render(context,request))

# this view returns a JSON list that is used for the right two menu bars of the app
def listJSON(request,what):
    
    professorNetID = request.session['netid']
    obj = dict()
    
    courseList = sections.objects.filter(professor__netID=professorNetID)     #find courses associated with loged-in professor
    
    semSem, semYear = tuple(request.GET['semStr'].split('_'))
    sectionsThisSem = courseList.filter(year=semYear).filter(semester=semSem)
    obj['semester'] = semSem
    obj['year'] = semYear
    obj['semStr'] = request.GET['semStr']
    
    if what == 'courses':
        obj['courses'] = list()
        for s in sectionsThisSem:
            obj['courses'].append(s.course.name)
    elif what == 'outcomes' or what == 'pis':
        courseName = request.GET['course'];
        obj['courseName'] = courseName
        
        section = sectionsThisSem.get(course__name=courseName)
        outcomeList = courseOutcomes.objects.filter(section=section)
        
        if what == 'outcomes':
            obj['outcomes'] = list()
            for o in outcomeList:
                obj['outcomes'].append(o.studentOutcome.outcomeLetter)
        
        elif what == 'pis':
            outcomeLetter = request.GET['outcome']
            outcome = outcomeList.get(studentOutcome__outcomeLetter=outcomeLetter)
            obj['outcome'] = outcomeLetter
            piList = performanceIndicators.objects.filter(outcome__pk=outcome.id)
            obj['pis'] = list()
            for p in piList:
                obj['pis'].append(p.name)
            
    return JsonResponse(obj)
    
    
def form(request,what):
    
    professorNetID = request.session['netid']
    obj = dict()
    
    
    # retreive the section
    sectionList = sections.objects.filter(professor__netID=professorNetID)     #find courses associated with loged-in professor
    semSem, semYear = tuple(request.GET['semStr'].split('_'))
    sectionsThisSem = sectionList.filter(year=semYear).filter(semester=semSem)
    section = sectionsThisSem.get(course__name=request.GET['course'])
    
    # retreive the outcome
    outcome = courseOutcomes.objects.get(section__pk=section.id, \
                    studentOutcome__outcomeLetter=request.GET['outcome'])
                                

    
    # retreive all performance levels
    perfLevList = performanceLevels.objects.all()
    
    # begin context ( more to be added along the way )
    context = {
        'semStr':request.GET['semStr'],
        'section':section,
        'outcome':outcome,
        'perfLevels':perfLevList,
    }
    
    if what == 'pi':
        template = loader.get_template('ABET_DB/pi.html')
        
        # if the pi is infact given
        if request.GET['pi'] != '~':
            
            # retreive the performance indicator
            pi = performanceIndicators.objects.get(outcome__pk=outcome.id, \
                                                    name=request.GET['pi'])
            context['pi'] = pi
            
            # retreive the rubrics
            rubricList = rubrics.objects.filter(performanceIndicator__pk=pi.id)
            context['rubrics'] = rubricList
    
    elif what == 'outcome': 
        template = loader.get_template('ABET_DB/outcome.html')
        
        odList = outcomeData.objects.filter(outcome__pk=outcome.id)
        print 'OD List:::'
        print(odList)
        context['outcomeData'] = odList
    
    else:
        raise ValueError("form url not 'pi' or 'outcome'")
    
    return HttpResponse(template.render(context,request))


def submit(request,what):
    
    try:
        professorNetID = request.session['netid']
    except KeyError:
        raise KeyError("Professor's netid not in session data.")
    
    
    sectionList = sections.objects.filter(professor__netID=professorNetID)
    
    if len(sectionList) == 0:
        raise ABET_Error('Section List Empty for Professor')
        
    try:
        sectionID = request.POST['sectionID']
    except KeyError:
        raise ValueError('sectionID not in POST data')
        
    section = sectionList.get(pk=sectionID)
    courseOutcomeList = courseOutcomes.objects.filter(section=section)
    outcomeLetter = request.POST['outcome']
    courseOutcome = courseOutcomeList.get(studentOutcome__outcomeLetter=outcomeLetter)

    perfLevels = performanceLevels.objects.all()
    
    data = {
       "professorNetID":professorNetID,
       "course":section.course.name,
       "outcome":courseOutcome.studentOutcome.outcomeLetter,
    }
    
    
    # SUBMIT PI DATA
    if what == 'pi':
        
        PIList = performanceIndicators.objects.filter(outcome=courseOutcome)
        
        if request.POST['pi'] == '': # create a new pi and rubrics
            # return an error if the name is already taken
            if PIList.filter(name=request.POST['newName']).count() != 0:
                return JsonResponse({
                    sucess:False,
                    error:"nameTaken",
                })
            p = performanceIndicators(name=request.POST['newName'])
            p.outcome = courseOutcome
        else:
            p = PIList.get(name=request.POST['pi'])
            if request.POST['newName'] != request.POST['pi']:
                # return an error if the name is already taken
                if PIList.filter(name=request.POST['newName']).count() != 0:
                    return JsonResponse({
                        "success":False,
                        "error":"nameTaken"
                    })
                p.name = request.POST['newName']
                
        p.weight = float(request.POST['weight'])
        p.description = request.POST['description']
        p.save()
        
        data['pi'] = p.name
            
        #update PI info
        
        # populate rubric list if empty
        rubricList = rubrics.objects.filter(performanceIndicator=p)
        if len(rubricList) == 0:
            for pl in perfLevels:
                r = rubrics(performanceLevel=pl,performanceIndicator=p)
                r.save()
            rubricList = rubrics.objects.filter(performanceIndicator=p)
            
        for pl in perfLevels:
            a = str(pl.achievementLevel)
            r = rubricList.get(performanceLevel__achievementLevel=pl.achievementLevel)
            
            if request.POST['r_'+a+'_upper']: r.gradeTopBound = int(request.POST['r_'+a+'_upper'])
            if request.POST['r_'+a+'_lower']: r.gradeLowerBound = int(request.POST['r_'+a+'_lower'])
            if request.POST['r_'+a+'_num']:   r.numStudents = int(request.POST['r_'+a+'_num'])
            r.description = request.POST['r_'+a+'_desc']
            
            r.save()
            
    # SUBMIT OUTCOME DATA
    elif what == 'outcome':         #submitting aggragate outcomeData form
        
        perSectionOutcomeData = outcomeData.objects.filter(outcome=courseOutcome)
        
        if len(perSectionOutcomeData) == 0:         #object doesnt exist, must create object
            for pl in perfLevels:
                a = str(pl.achievementLevel)
                o = outcomeData(outcome=courseOutcome, performanceLevel=pl)
                if request.POST['od_'+a+'_num']: o.numberAchieved = request.POST['od_'+a+'_num']
                o.save()
                
        else:                                       #object already exists
            assert len(perSectionOutcomeData) == len(perfLevels), "Corrupted outcomeData"
            
            for pl in perfLevels:
                a = str(pl.achievementLevel)
                o = perSectionOutcomeData.get(performanceLevel__achievementLevel=a)
                if request.POST['od_'+a+'_num']: o.numberAchieved = request.POST['od_'+a+'_num']
                o.save()
                
        courseOutcome.narrativeSummary = request.POST['narrSum']
        courseOutcome.save()
        
    # DELETE A PERFORMANCE INDICATOR
    elif what == 'deletePI':        #delete button pushed
        
        PIList = performanceIndicators.objects.filter(outcome=courseOutcome)
        
        if len(PIList) == 0:
            raise ValueError("Atempting to delete non-existant PI")
        
        p = PIList.get(name=request.POST['pi'])
        rubricList = rubrics.objects.filter(performanceIndicator=p)
        
        if len(rubricList) == 0:
            raise ValueError("Atempting to delete non-existant rubrics")
            
        rubricList.delete()
        p.delete()
        
    else:
        raise ValueError("Bad Url in SubmitForm")
    
    return JsonResponse(data)

  
def populate(request):
    #add performanceLevels
    excede = performanceLevels(achievementLevel=0, description='Exceded Expectations')
    met = performanceLevels(achievementLevel=1, description='Met Expectations')
    didNotMeet = performanceLevels(achievementLevel=2, description='Did Not Meet Expectations')
    excede.save()
    met.save()
    didNotMeet.save()
    
    #add professors
    jkohann = professors(netID='jkohann', fn='Julian', ln='Kohann')
    bvz = professors(netID='bvz', fn='Brad', ln='VZ')
    ahnilica = professors(netID='ahnilica', fn='Andrew', ln='Hnilica')
    stonecoldhughes = professors(netID='stonecoldhughes', fn='Harry', ln='Hughes')
    jkohann.save()
    bvz.save()
    ahnilica.save()
    stonecoldhughes.save()
    
    #add courses
    cs360 = courses(name='cs360', description='Systems Programing')
    cs140 = courses(name='cs140', description='Algorithms 1')
    cs420 = courses(name='cs420', description='Bio Inspired Computing')
    cs401 = courses(name='cs401', description='Sr Design Theory')
    cs402 = courses(name='cs402', description='Sr Design Practicum')
    cs302 = courses(name='cs302', description='Algorithms 2')
    cs102 = courses(name='cs102', description='Intro')
    cs360.save()
    cs140.save()
    cs420.save()
    cs401.save()
    cs402.save()
    cs302.save()
    cs102.save()
    
    #add outcomes
    a = studentOutcomes(outcomeLetter='A', description='outcome A')
    b = studentOutcomes(outcomeLetter='B', description='outcome B')
    c = studentOutcomes(outcomeLetter='C', description='outcome C')
    d = studentOutcomes(outcomeLetter='D', description='outcome D')
    e = studentOutcomes(outcomeLetter='E', description='outcome E')
    f = studentOutcomes(outcomeLetter='F', description='outcome F')
    g = studentOutcomes(outcomeLetter='G', description='outcome G')
    h = studentOutcomes(outcomeLetter='H', description='outcome H')
    i = studentOutcomes(outcomeLetter='I', description='outcome I')
    j = studentOutcomes(outcomeLetter='J', description='outcome J')
    a.save()
    b.save()
    c.save()
    d.save()
    e.save()
    f.save()
    g.save()
    h.save()
    i.save()
    j.save()
    
    #add sections
    secA = sections(course=cs360, professor=jkohann, year=2016, semester='spring')
    secB = sections(course=cs140, professor=jkohann, year=2016, semester='spring')
    secC = sections(course=cs420, professor=jkohann, year=2016, semester='spring')
    secD = sections(course=cs360, professor=jkohann, year=2015, semester='spring')
    secE = sections(course=cs140, professor=jkohann, year=2015, semester='spring')
    secF = sections(course=cs420, professor=jkohann, year=2015, semester='spring')
    secG = sections(course=cs360, professor=jkohann, year=2015, semester='fall')
    secH = sections(course=cs140, professor=jkohann, year=2015, semester='fall')
    secI = sections(course=cs420, professor=jkohann, year=2015, semester='fall')
    secJ = sections(course=cs360, professor=jkohann, year=2014, semester='spring')
    secA.save()
    secB.save()
    secC.save()
    secD.save()
    secE.save()
    secF.save()
    secG.save()
    secH.save()
    secI.save()
    secJ.save()
    
    #add courseOutcomes
    co1 = courseOutcomes(narrativeSummary='co1', studentOutcome=a, section=secA)
    co2 = courseOutcomes(narrativeSummary='co2', studentOutcome=b, section=secA)
    co3 = courseOutcomes(narrativeSummary='co3', studentOutcome=c, section=secA)
    co4 = courseOutcomes(narrativeSummary='co4', studentOutcome=d, section=secA)
    co5 = courseOutcomes(narrativeSummary='co5', studentOutcome=e, section=secA)
    co6 = courseOutcomes(narrativeSummary='co6', studentOutcome=a, section=secB)
    co7 = courseOutcomes(narrativeSummary='co7', studentOutcome=f, section=secB)
    co8 = courseOutcomes(narrativeSummary='co8', studentOutcome=g, section=secB)
    co9 = courseOutcomes(narrativeSummary='co9', studentOutcome=a, section=secC)
    co1.save()
    co2.save()
    co3.save()
    co4.save()
    co5.save()
    co6.save()
    co7.save()
    co8.save()
    co9.save()
    
    #add performanceIndicators
    one = performanceIndicators(name='one', weight=0.5, description='PI One', outcome=co1)
    two = performanceIndicators(name='two', weight=0.5, description='PI Two', outcome=co1)
    three = performanceIndicators(name='three', weight=0.5, description='PI three', outcome=co2)
    four = performanceIndicators(name='four', weight=0.5, description='PI four', outcome=co2)
    five = performanceIndicators(name='five', weight=0.5, description='PI five', outcome=co2)
    six = performanceIndicators(name='six', weight=0.5, description='PI six', outcome=co3)
    seven = performanceIndicators(name='seven', weight=0.5, description='PI seven', outcome=co4)
    eight = performanceIndicators(name='eight', weight=0.5, description='PI eight', outcome=co4)
    nine = performanceIndicators(name='nine', weight=0.5, description='PI nine', outcome=co4)
    ten = performanceIndicators(name='ten', weight=0.5, description='PI ten', outcome=co6)
    one.save()
    two.save()
    three.save()
    four.save()
    five.save()
    six.save()
    seven.save()
    eight.save()
    nine.save()
    ten.save()
    
    #add rubrics
    rubA = rubrics(gradeTopBound=100, gradeLowerBound=90, description='Rubric A', numStudents=50, performanceLevel=excede, performanceIndicator=one)
    rubB = rubrics(gradeTopBound=90, gradeLowerBound=80, description='Rubric B', numStudents=50, performanceLevel=met, performanceIndicator=one)
    rubC = rubrics(gradeTopBound=80, gradeLowerBound=70, description='Rubric C', numStudents=50, performanceLevel=didNotMeet, performanceIndicator=one)
    
    rubE = rubrics(gradeTopBound=100, gradeLowerBound=90, description='Rubric E', numStudents=50, performanceLevel=excede, performanceIndicator=two)
    rubF = rubrics(gradeTopBound=90, gradeLowerBound=80, description='Rubric F', numStudents=50, performanceLevel=met, performanceIndicator=two)
    rubG = rubrics(gradeTopBound=80, gradeLowerBound=70, description='Rubric G', numStudents=50, performanceLevel=didNotMeet, performanceIndicator=two)
    
    rubI = rubrics(gradeTopBound=100, gradeLowerBound=90, description='Rubric I', numStudents=50, performanceLevel=excede, performanceIndicator=three)
    rubJ = rubrics(gradeTopBound=90, gradeLowerBound=80, description='Rubric J', numStudents=50, performanceLevel=met, performanceIndicator=three)
    rubK = rubrics(gradeTopBound=80, gradeLowerBound=70, description='Rubric K', numStudents=50, performanceLevel=didNotMeet, performanceIndicator=three)
    
    rubM = rubrics(gradeTopBound=100, gradeLowerBound=90, description='rubric m', numStudents=50, performanceLevel=excede, performanceIndicator=four)
    rubN = rubrics(gradeTopBound=90, gradeLowerBound=80, description='Rubric N', numStudents=50, performanceLevel=met, performanceIndicator=four)
    rubO = rubrics(gradeTopBound=80, gradeLowerBound=70, description='Rubric O', numStudents=50, performanceLevel=didNotMeet, performanceIndicator=four)
    rubA.save()
    rubB.save()
    rubC.save()
  
    rubE.save()
    rubF.save()
    rubG.save()
   
    rubI.save()
    rubJ.save()
    rubK.save()
   
    rubM.save()
    rubN.save()
    rubO.save()
    return HttpResponse("Populated Database")

  
def clearDB(request):
    professors.objects.all().delete()
    courses.objects.all().delete()
    studentOutcomes.objects.all().delete()
    performanceLevels.objects.all().delete()
    rubrics.objects.all().delete()
    performanceIndicators.objects.all().delete()
    sections.objects.all().delete()
    courseOutcomes.objects.all().delete()
    outcomeData.objects.all().delete()
    return HttpResponse("Cleared Database")
    
    
