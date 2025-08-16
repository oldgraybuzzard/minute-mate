#!/usr/bin/env python3
"""
Test script for large transcript processing
"""

import os
import sys
import logging
from ai_processor import AIProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_large_transcript_processing():
    """Test the new chunking functionality with a large transcript"""
    
    # Create a sample large transcript (simulate your 121K character transcript)
    sample_transcript = """
Meeting Minutes - Board Meeting
Date: August 16, 2025
Time: 2:00 PM
Location: Conference Room A

Attendees:
- John Smith, President
- Jane Doe, Secretary  
- Bob Johnson, Treasurer
- Alice Wilson, Board Member
- Mike Davis, Board Member

Meeting called to order at 2:00 PM by President John Smith.

AGENDA ITEM 1: Review of Previous Minutes
President Smith: Good afternoon everyone. Let's begin with the review of our previous meeting minutes from July 15th. Jane, could you please summarize the key points?

Secretary Doe: Thank you, Mr. President. The July meeting covered three main areas: budget approval for Q3, the new employee handbook updates, and the facility expansion project. All motions from that meeting were approved unanimously.

Board Member Wilson: I'd like to add that the facility expansion timeline has been accelerated due to the contractor's availability.

President Smith: Thank you, Alice. Are there any corrections or additions to the July minutes?

[No corrections noted]

Motion to approve July minutes made by Treasurer Johnson, seconded by Board Member Davis. Motion carried unanimously.

AGENDA ITEM 2: Financial Report
Treasurer Johnson: I'll present our Q2 financial results. Revenue for the quarter was $2.4 million, representing a 15% increase over Q2 last year. Operating expenses were $1.8 million, giving us a net profit of $600,000 for the quarter.

President Smith: That's excellent news, Bob. What are the main drivers of this revenue increase?

Treasurer Johnson: The primary factors are increased client retention, successful launch of our new service line, and improved operational efficiency. Client retention is up to 94%, which is the highest we've seen in five years.

Board Member Davis: What about our cash flow position?

Treasurer Johnson: Cash flow remains strong. We have $3.2 million in operating cash, and our credit line remains untouched. We're well-positioned for the facility expansion project.

Secretary Doe: Are there any concerns about the upcoming Q3 projections?

Treasurer Johnson: Q3 typically sees a seasonal dip, but based on current contracts and pipeline, we're projecting only a 5% decrease from Q2, which is better than historical averages.

Motion to accept the financial report made by Board Member Wilson, seconded by Secretary Doe. Motion carried unanimously.

AGENDA ITEM 3: Facility Expansion Project Update
President Smith: Let's move to the facility expansion update. As Alice mentioned earlier, we have some timeline changes.

Board Member Wilson: The contractor, BuildRight Construction, has informed us they can begin work two weeks earlier than originally planned. This would move our start date from September 15th to September 1st.

Board Member Davis: What are the implications of this accelerated timeline?

Board Member Wilson: The main benefit is completion by December 15th instead of year-end, which means we can move into the new space before the holidays. However, we'll need to expedite some permit approvals and material orders.

Secretary Doe: Have we confirmed all permits will be ready?

Board Member Wilson: I've been working with the city planning office. They've assured me that if we submit the final documents by August 25th, permits will be approved by August 30th.

President Smith: What about the budget impact?

Treasurer Johnson: The accelerated timeline actually saves us about $15,000 in carrying costs, but we may need to pay a 5% premium on some materials for expedited delivery. Net effect should be roughly neutral.

Board Member Davis: I move that we approve the accelerated timeline for the facility expansion project, contingent on permit approval by August 30th.

Board Member Wilson: I second the motion.

President Smith: All in favor? [All hands raised] Motion carried unanimously.

AGENDA ITEM 4: New Employee Handbook
Secretary Doe: The updated employee handbook has been reviewed by our legal counsel and HR consultant. Key changes include updated remote work policies, enhanced diversity and inclusion guidelines, and revised performance review procedures.

President Smith: What feedback did we receive from the employee survey?

Secretary Doe: Overall response was very positive. 87% of employees supported the remote work policy updates, and 92% felt the diversity and inclusion changes were important and well-crafted.

Board Member Davis: Were there any concerns raised?

Secretary Doe: The main concern was about the performance review frequency. Some employees preferred annual reviews instead of semi-annual. However, management believes semi-annual reviews provide better feedback and development opportunities.

Board Member Wilson: I agree with management's position. More frequent feedback typically leads to better performance and job satisfaction.

Treasurer Johnson: What's the implementation timeline?

Secretary Doe: We plan to roll out the new handbook on September 1st, coinciding with our Q3 kickoff. All employees will receive training on the new policies during the first two weeks of September.

Motion to approve the new employee handbook made by Treasurer Johnson, seconded by Board Member Wilson. Motion carried unanimously.

AGENDA ITEM 5: Strategic Planning for 2026
President Smith: Looking ahead to next year, we need to begin our strategic planning process. I'd like to form a strategic planning committee.

Board Member Davis: What would be the scope and timeline for this committee?

President Smith: The committee would develop our 2026 strategic plan, including growth targets, new market opportunities, and operational improvements. I'd like the plan completed by November 30th for board approval in December.

Board Member Wilson: Who would serve on this committee?

President Smith: I propose the committee consist of myself, Bob as treasurer, one additional board member, and two senior staff members from operations and sales.

Secretary Doe: I'd like to volunteer to serve as the additional board member.

President Smith: Excellent, Jane. Bob, are you available to participate?

Treasurer Johnson: Yes, I can commit the time needed.

Board Member Davis: What about external consultants?

President Smith: We may engage a strategic planning consultant if needed, but I'd like to start with internal resources and see how far we can get.

Motion to establish a strategic planning committee consisting of President Smith, Treasurer Johnson, Secretary Doe, and two senior staff members, made by Board Member Wilson, seconded by Board Member Davis. Motion carried unanimously.

AGENDA ITEM 6: Technology Infrastructure Upgrade
Board Member Davis: I'd like to propose a comprehensive review of our technology infrastructure. Our current systems are becoming outdated and may not support our growth plans.

President Smith: What specific areas are you concerned about?

Board Member Davis: Our customer relationship management system is seven years old, our accounting software needs updating, and our network infrastructure may not handle the increased capacity from the facility expansion.

Treasurer Johnson: What's the estimated cost for these upgrades?

Board Member Davis: I've received preliminary quotes ranging from $150,000 to $250,000, depending on the scope. However, this investment could improve efficiency by 20-30% and reduce ongoing maintenance costs.

Secretary Doe: Have we considered cloud-based solutions?

Board Member Davis: Yes, cloud solutions are included in the quotes. They offer better scalability and lower upfront costs, though ongoing subscription fees need to be factored in.

Board Member Wilson: I think this is a critical investment. Our current systems are holding us back.

President Smith: I agree this needs attention. Mike, can you prepare a detailed proposal with specific recommendations and ROI analysis?

Board Member Davis: I'll have a comprehensive proposal ready for our September meeting.

Motion to authorize Board Member Davis to develop a detailed technology infrastructure upgrade proposal, made by Secretary Doe, seconded by Treasurer Johnson. Motion carried unanimously.

AGENDA ITEM 7: New Business
President Smith: Are there any new business items to discuss?

Board Member Wilson: I'd like to mention that we've received an inquiry from a potential acquisition target. It's a small company in our industry with complementary services.

President Smith: Can you provide more details?

Board Member Wilson: The company has annual revenue of about $800,000 and serves a geographic market we don't currently cover. The owner is looking to retire and has approached us about a possible acquisition.

Treasurer Johnson: What would be the financial implications?

Board Member Wilson: Very preliminary discussions suggest a purchase price in the $1.2 to $1.5 million range. The company is profitable and would add about 15 new clients to our base.

Secretary Doe: This seems like it could fit well with our strategic planning discussions.

President Smith: I agree. Alice, can you gather more detailed information for the strategic planning committee to review?

Board Member Wilson: Absolutely. I'll request financial statements and operational details.

Board Member Davis: We should also consider how this would integrate with our technology upgrade plans.

President Smith: Good point, Mike. Let's make sure the strategic planning committee coordinates with your technology proposal.

No formal motion required - information gathering authorized.

AGENDA ITEM 8: Executive Session
President Smith: I'd like to call for a brief executive session to discuss a personnel matter.

[Executive session held from 4:15 PM to 4:30 PM - details confidential]

AGENDA ITEM 9: Return to Open Session
President Smith: We're back in open session. During executive session, the board discussed and approved a salary adjustment for our operations manager, effective September 1st.

ADJOURNMENT
President Smith: Is there any other business to come before the board today?

[No additional business]

Motion to adjourn made by Treasurer Johnson, seconded by Board Member Davis. Motion carried unanimously.

Meeting adjourned at 4:35 PM.

Next meeting scheduled for September 20, 2025, at 2:00 PM in Conference Room A.

Minutes recorded by Jane Doe, Secretary
Approved by John Smith, President

Action Items Summary:
1. Board Member Wilson - Submit final facility expansion documents by August 25th
2. Secretary Doe - Implement new employee handbook by September 1st  
3. Strategic Planning Committee - Complete 2026 strategic plan by November 30th
4. Board Member Davis - Prepare technology infrastructure proposal for September meeting
5. Board Member Wilson - Gather acquisition target information for strategic planning committee

Key Decisions:
1. Approved July meeting minutes
2. Accepted Q2 financial report
3. Approved accelerated facility expansion timeline
4. Approved new employee handbook
5. Established strategic planning committee
6. Authorized technology infrastructure upgrade proposal development
7. Approved operations manager salary adjustment

Financial Summary:
- Q2 Revenue: $2.4 million (15% increase YoY)
- Q2 Net Profit: $600,000
- Operating Cash: $3.2 million
- Facility expansion budget impact: Neutral
- Technology upgrade estimate: $150,000-$250,000
- Potential acquisition cost: $1.2-$1.5 million
""" * 10  # Multiply to create a large transcript

    logger.info(f"Created test transcript with {len(sample_transcript)} characters")
    
    # Initialize AI processor
    processor = AIProcessor()
    
    if not processor.is_available():
        logger.error("AI processor not available - check OpenAI API key")
        return
    
    logger.info(f"Using model: {processor.model}")
    logger.info(f"Max context chars: {processor.max_context_chars}")
    
    # Process the large transcript
    try:
        result = processor.process_transcript(sample_transcript, "large_test_meeting.txt")
        
        logger.info("Processing completed successfully!")
        logger.info(f"Result keys: {list(result.keys())}")
        
        if 'processing_stats' in result:
            stats = result['processing_stats']
            logger.info(f"Processing stats: {stats}")
        
        # Print summary
        print("\n" + "="*50)
        print("PROCESSING SUMMARY")
        print("="*50)
        print(f"Original transcript: {len(sample_transcript):,} characters")
        print(f"Model used: {processor.model}")
        print(f"Processing method: {result.get('meeting_info', {}).get('processing_method', 'Standard')}")
        
        if 'attendees' in result:
            print(f"Attendees found: {len(result['attendees'])}")
        if 'agenda_items' in result:
            print(f"Agenda items: {len(result['agenda_items'])}")
        if 'motions' in result:
            print(f"Motions: {len(result['motions'])}")
        if 'action_items' in result:
            print(f"Action items: {len(result['action_items'])}")
        
        return result
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        return None

if __name__ == "__main__":
    test_large_transcript_processing()
